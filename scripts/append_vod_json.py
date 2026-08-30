#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import quote


def safe(value, fallback=''):
    return str(value or fallback).replace('\n', ' ').replace('"', "'").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--m3u', type=Path, required=True)
    parser.add_argument('--vod-json', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    user, password = quote(args.username), quote(args.password)
    lines = args.m3u.read_text(errors='ignore').splitlines()
    existing = {line.split(',', 1)[-1].strip() for line in lines if line.startswith('#EXTINF:')}
    items = json.loads(args.vod_json.read_text())
    added = 0
    for item in items if isinstance(items, list) else []:
        stream_id = item.get('stream_id')
        if not stream_id:
            continue
        name = safe(item.get('name'), f'Movie {stream_id}')
        if name in existing:
            continue
        ext = safe(item.get('container_extension'), 'mp4')
        group = 'VOD / Movies / ' + safe(item.get('category_name'), 'Uncategorised')
        logo = safe(item.get('stream_icon'))
        attrs = [f'tvg-name="{name}"', f'group-title="{group}"']
        if logo:
            attrs.append(f'tvg-logo="{logo}"')
        attrs.append('media-type="movie"')
        lines.append('#EXTINF:-1 ' + ' '.join(attrs) + ',' + name)
        lines.append(f'{base}/movie/{user}/{password}/{stream_id}.{ext}')
        existing.add(name)
        added += 1
    args.out.write_text('\n'.join(lines) + '\n')
    print(json.dumps({'source_items': len(items) if isinstance(items, list) else 0, 'movies_added': added, 'output_bytes': args.out.stat().st_size}))


if __name__ == '__main__':
    main()
