#!/usr/bin/env python3
"""Remove TV-series/show VOD entries from an M3U without touching Live TV or Movies."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


def is_series(header: str, url: str) -> bool:
    attrs = dict(ATTR_RE.findall(header))
    group = attrs.get('group-title', '')
    return (
        attrs.get('media-type', '').lower() in {'episode', 'series'}
        or group.lower().startswith('series/')
        or 'tv shows' in group.lower()
        or '/series/' in url.lower()
    )


def filter_playlist(input_path: Path, output_path: Path) -> dict[str, int]:
    kept = removed = live = movies = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open('r', encoding='utf-8', errors='replace') as src, output_path.open('w', encoding='utf-8', newline='\n') as dst:
        pending: str | None = None
        for raw in src:
            line = raw.rstrip('\r\n')
            if line.startswith('#EXTINF:'):
                if pending is not None:
                    dst.write(pending + '\n')
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
            if is_series(pending, line):
                removed += 1
            else:
                dst.write(pending + '\n' + line + '\n')
                kept += 1
                attrs = dict(ATTR_RE.findall(pending))
                if 'movie' in attrs.get('group-title', '').lower() or 'movies' in attrs.get('group-title', '').lower(): movies += 1
                else: live += 1
            pending = None
        if pending is not None:
            dst.write(pending + '\n')
    return {'kept': kept, 'removed_series': removed, 'live': live, 'movies': movies, 'bytes': output_path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(filter_playlist(args.input, args.output))


if __name__ == '__main__':
    main()
