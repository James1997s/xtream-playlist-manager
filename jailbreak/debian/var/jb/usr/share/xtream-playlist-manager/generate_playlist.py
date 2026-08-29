#!/usr/bin/env python3
"""Generate an Xtream live-TV M3U playlist from environment variables."""
from __future__ import annotations

import os
import sys
from urllib.parse import quote, urlparse, urlunparse
import requests


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def clean_base(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw
    parsed = urlparse(raw)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def main() -> None:
    base = clean_base(required("XTREAM_BASE_URL"))
    username = required("XTREAM_USERNAME")
    password = required("XTREAM_PASSWORD")
    timeout = int(os.environ.get("XTREAM_TIMEOUT", "30"))

    api = f"{base}/player_api.php"
    params = {"username": username, "password": password, "action": "get_live_streams"}
    response = requests.get(api, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise SystemExit("Xtream server returned an unexpected response; check the details.")

    # Xtream stream URLs normally contain the account credentials because IPTV
    # players need them to authenticate. Do not publish this file if that is
    # unacceptable; use a private/proxy arrangement instead.
    lines = ["#EXTM3U", f"# Generated from Xtream API; streams: {len(payload)}"]
    for item in payload:
        stream_id = item.get("stream_id")
        name = str(item.get("name") or f"Channel {stream_id}").replace("\n", " ")
        logo = str(item.get("stream_icon") or "")
        group = str(item.get("category_name") or "Live TV").replace("\n", " ")
        if not stream_id:
            continue
        attrs = [f'tvg-name="{name.replace(chr(34), chr(39))}"', f'group-title="{group.replace(chr(34), chr(39))}"']
        if logo:
            attrs.append(f'tvg-logo="{logo.replace(chr(34), chr(39))}"')
        lines.append(f"#EXTINF:-1 {' '.join(attrs)},{name}")
        lines.append(f"{base}/live/{quote(username)}/{quote(password)}/{stream_id}.m3u8")

    output = os.environ.get("OUTPUT_FILE", "playlist.m3u")
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"Wrote {len(payload)} streams to {output}")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Network/API error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except ValueError as exc:
        print(f"Invalid JSON from Xtream server: {exc}", file=sys.stderr)
        raise SystemExit(1)
