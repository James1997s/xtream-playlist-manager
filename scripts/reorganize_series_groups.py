#!/usr/bin/env python3
"""Organize M3U TV episodes into VOD / TV Shows / category / show / season groups."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')

def safe(value: str) -> str:
    return value.replace('"', "'").replace('\n', ' ').strip()

def organize(path: Path, out: Path) -> tuple[int, int]:
    lines = path.read_text(errors='ignore').splitlines()
    changed = 0
    episodes = 0
    result = []
    for line in lines:
        if line.startswith('#EXTINF:') and 'media-type="episode"' in line:
            attrs = dict(ATTR_RE.findall(line))
            show = safe(attrs.get('tv-show', 'Unknown Show'))
            season_raw = attrs.get('season', '1')
            try:
                season = int(season_raw)
            except ValueError:
                season = 1
            old_group = attrs.get('group-title', '')
            prefix = old_group.split(' / TV Shows / ', 1)[0] if ' / TV Shows / ' in old_group else 'VOD'
            new_group = f'{prefix} / TV Shows / {show} / Season {season:02d}'
            updated = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', line, count=1)
            if updated != line:
                changed += 1
            episodes += 1
            result.append(updated)
        else:
            result.append(line)
    out.write_text('\n'.join(result) + '\n')
    return episodes, changed

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    episodes, changed = organize(args.input, args.output)
    print(f'episodes={episodes} groups_updated={changed} output={args.output}')

if __name__ == '__main__':
    main()
