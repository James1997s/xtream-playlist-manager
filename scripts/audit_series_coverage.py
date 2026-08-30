#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from collections import defaultdict
from pathlib import Path

def norm(value):
    value = re.sub(r'[^a-z0-9]+', ' ', (value or '').lower())
    return ' '.join(value.split())

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--series-json', type=Path, required=True)
    p.add_argument('--details-jsonl', type=Path, required=True)
    p.add_argument('--m3u', type=Path, required=True)
    args = p.parse_args()
    series = json.loads(args.series_json.read_text())
    detail_rows = []
    for line in args.details_jsonl.read_text(errors='ignore').splitlines():
        if not line.strip():
            continue
        try:
            detail_rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    playlist_shows = defaultdict(int)
    for line in args.m3u.read_text(errors='ignore').splitlines():
        if 'media-type="episode"' not in line:
            continue
        match = re.search(r'tv-show="([^"]+)"', line)
        if match: playlist_shows[norm(match.group(1))] += 1
    fetched_shows = {}
    fetched_episodes = 0
    for row in detail_rows:
        show = row.get('show') or {}
        detail = row.get('detail') or {}
        key = norm(show.get('name'))
        episodes = detail.get('episodes') or {}
        if isinstance(episodes, dict):
            count = sum(len(items or []) for items in episodes.values())
        elif isinstance(episodes, list):
            count = len(episodes)
        else:
            count = 0
        fetched_shows[key] = {'name': show.get('name'), 'episodes': count}
        fetched_episodes += count
    represented = sum(1 for item in series if norm(item.get('name')) in playlist_shows)
    playlist_episode_count = sum(playlist_shows.values())
    missing = [item.get('name') for item in series if norm(item.get('name')) not in playlist_shows]
    partial = [item.get('name') for item in series if norm(item.get('name')) in fetched_shows and playlist_shows[norm(item.get('name'))] < fetched_shows[norm(item.get('name'))]['episodes']]
    summary = {'xtream_series': len(series), 'series_details_fetched': len(detail_rows), 'series_represented_in_playlist': represented, 'series_missing_from_playlist': len(missing), 'playlist_episode_entries': playlist_episode_count, 'episodes_from_fetched_details': fetched_episodes, 'partial_series_count': len(partial), 'missing_sample': missing[:30], 'partial_sample': partial[:30]}
    print(json.dumps(summary, indent=2))

if __name__ == '__main__': main()
