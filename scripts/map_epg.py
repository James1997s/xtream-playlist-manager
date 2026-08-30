#!/usr/bin/env python3
"""Map M3U channel names to XMLTV channel IDs.

The script is intentionally review-first: only high-confidence matches should be
written back into an M3U automatically. Medium-confidence matches include
alternatives for human review; low-confidence channels remain unmatched.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

NOISE = {
    "4k", "8k", "uhd", "fhd", "hd", "sd", "lhd", "hevc", "h265", "h264",
    "1080p", "720p", "576p", "480p", "east", "west", "central", "backup",
    "test", "channel", "tv", "live", "plus", "official", "alt", "feed",
}
COUNTRY_PREFIXES = {
    "usa", "us", "uk", "gb", "canada", "ca", "australia", "au", "india",
    "ireland", "france", "germany", "italy", "spain", "portugal", "international",
}

def normalize(value: str, strip_country: bool = False) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"https?://\S+", " ", value.lower())
    value = re.sub(r"\[[^\]]*\]|\([^)]*\)|\{[^}]*\}", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = [token for token in value.split() if token not in NOISE]
    if strip_country and tokens and tokens[0] in COUNTRY_PREFIXES:
        tokens = tokens[1:]
    return " ".join(tokens)

def parse_m3u(path: Path) -> list[dict[str, str]]:
    records = []
    for line in path.read_text(errors="ignore").splitlines():
        if not line.startswith("#EXTINF:"):
            continue
        comma = line.find(",")
        title = line[comma + 1:].strip() if comma >= 0 else ""
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', line))
        records.append({"title": title, "tvg_id": attrs.get("tvg-id", ""), "group": attrs.get("group-title", "")})
    return records

def parse_xmltv(path: Path) -> list[dict[str, object]]:
    channels = []
    for event, element in ET.iterparse(path, events=("end",)):
        if element.tag == "channel":
            names = [node.text.strip() for node in element.findall("display-name") if node.text and node.text.strip()]
            if names:
                channels.append({"id": element.attrib.get("id", ""), "names": names})
            element.clear()
    return channels

def score_pair(source: str, candidate: str) -> tuple[float, str]:
    if not source or not candidate:
        return 0.0, "empty"
    if source == candidate:
        return 1.0, "exact-normalized"
    source_tokens, candidate_tokens = set(source.split()), set(candidate.split())
    overlap = len(source_tokens & candidate_tokens) / max(len(source_tokens | candidate_tokens), 1)
    sequence = SequenceMatcher(None, source, candidate).ratio()
    containment = 1.0 if source in candidate or candidate in source else 0.0
    score = (sequence * 0.55) + (overlap * 0.35) + (containment * 0.10)
    return score, "fuzzy-token-sequence"

def make_index(channels: list[dict[str, object]]) -> tuple[dict[str, list[int]], list[dict[str, object]]]:
    prepared = []
    index: dict[str, list[int]] = defaultdict(list)
    for number, channel in enumerate(channels):
        names = []
        for name in channel["names"]:  # type: ignore[index]
            names.extend([normalize(name), normalize(name, strip_country=True)])
        names = sorted({name for name in names if name})
        prepared.append({**channel, "normalized": names})
        for name in names:
            for token in set(name.split()):
                if len(token) >= 2:
                    index[token].append(number)
    return index, prepared

def map_channels(m3u_records: list[dict[str, str]], channels: list[dict[str, object]], auto_threshold: float, review_threshold: float) -> list[dict[str, object]]:
    token_index, prepared = make_index(channels)
    output = []
    for record in m3u_records:
        source_names = [normalize(record["title"]), normalize(record["title"], strip_country=True)]
        candidate_ids = set()
        for source in source_names:
            for token in set(source.split()):
                candidate_ids.update(token_index.get(token, []))
        candidates = []
        for candidate_id in candidate_ids:
            channel = prepared[candidate_id]
            best = max((score_pair(source, name) for source in source_names for name in channel["normalized"]), key=lambda item: item[0], default=(0.0, "none"))
            candidates.append((best[0], best[1], channel))
        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, reason, best_channel = candidates[0] if candidates else (0.0, "no-shared-tokens", {"id": "", "names": []})
        if best_score >= auto_threshold:
            confidence = "high"
        elif best_score >= review_threshold:
            confidence = "review"
        else:
            confidence = "unmatched"
        alternatives = [
            {"xmltv_id": item[2]["id"], "xmltv_name": item[2]["names"][0], "score": round(item[0], 4)}
            for item in candidates[1:4]
        ]
        output.append({
            "m3u_title": record["title"],
            "m3u_tvg_id": record["tvg_id"],
            "group": record["group"],
            "xmltv_id": best_channel.get("id", "") if confidence != "unmatched" else "",
            "xmltv_name": best_channel.get("names", [""])[0] if confidence != "unmatched" else "",
            "score": round(best_score, 4),
            "confidence": confidence,
            "reason": reason,
            "alternatives": alternatives,
        })
    return output

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m3u", type=Path, required=True)
    parser.add_argument("--xmltv", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("epg-map.json"))
    parser.add_argument("--auto-threshold", type=float, default=0.92)
    parser.add_argument("--review-threshold", type=float, default=0.80)
    args = parser.parse_args()
    mappings = map_channels(parse_m3u(args.m3u), parse_xmltv(args.xmltv), args.auto_threshold, args.review_threshold)
    args.out.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n")
    csv_path = args.out.with_suffix(".csv")
    with csv_path.open("w", newline="") as handle:
        fields = ["m3u_title", "m3u_tvg_id", "group", "xmltv_id", "xmltv_name", "score", "confidence", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in mappings)
    counts = defaultdict(int)
    for row in mappings:
        counts[row["confidence"]] += 1
    print(json.dumps({"mappings": len(mappings), "confidence": dict(counts), "json": str(args.out), "csv": str(csv_path)}))

if __name__ == "__main__":
    main()
