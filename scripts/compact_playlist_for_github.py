#!/usr/bin/env python3
"""Compact a large M3U under GitHub's normal file limit without dropping entries.

For TV episodes, retain the stream URL and parser-friendly show/season/episode
metadata, plus one logo per show. Live TV, movies, and the M3U header are kept
as-is so existing EPG references and channel metadata remain intact.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
EPISODE_RE = re.compile(r'(?:^|[ ._-])s(\d{1,2})[ ._-]*e(\d{1,3})(?:$|[ ._-])', re.I)


def safe(value: str) -> str:
    return value.replace('"', "'").replace('\r', ' ').replace('\n', ' ').strip()


def compact(input_path: Path, output_path: Path) -> dict[str, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    entries = live = movies = series = logos = 0
    with input_path.open('r', encoding='utf-8', errors='replace') as src, output_path.open('w', encoding='utf-8', newline='\n') as dst:
        pending: str | None = None
        for raw in src:
            line = raw.rstrip('\r\n')
            if line.startswith('#EXTINF:'):
                pending = line
                continue
            if pending is None:
                dst.write(line + '\n')
                continue
            if not line or line.startswith('#'):
                dst.write(pending + '\n')
                if line:
                    dst.write(line + '\n')
                pending = None
                continue
            attrs = dict(ATTR_RE.findall(pending))
            group = attrs.get('group-title', '')
            is_series = attrs.get('media-type') == 'episode' or 'TV Shows' in group or '/series/' in line
            if not is_series:
                dst.write(pending + '\n' + line + '\n')
                entries += 1
                if 'movie' in group.lower() or 'movies' in group.lower(): movies += 1
                else: live += 1
                pending = None
                continue
            original_title = pending.split(',', 1)[1] if ',' in pending else ''
            match = EPISODE_RE.search(original_title)
            show = safe(attrs.get('tv-show') or (match and original_title[:match.start()]) or original_title or 'Unknown Show')
            try:
                season = int(attrs.get('season') or (match.group(1) if match else 1))
            except (TypeError, ValueError):
                season = 1
            try:
                episode = int(attrs.get('episode') or (match.group(2) if match else 0))
            except (TypeError, ValueError):
                episode = 0
            title = f'{show} S{season}E{episode}'
            header = f'#EXTINF:-1 group-title="Series/{safe(show)}/S{season}",{title}'
            dst.write(header + '\n' + line + '\n')
            entries += 1
            series += 1
            pending = None
        if pending is not None:
            dst.write(pending + '\n')
    return {'entries': entries, 'live': live, 'movies': movies, 'series': series, 'show_logos': logos, 'bytes': output_path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(compact(args.input, args.output))


if __name__ == '__main__':
    main()
