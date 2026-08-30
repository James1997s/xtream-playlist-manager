#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import quote

def safe(value, fallback=''):
    return str(value or fallback).replace('\n', ' ').replace('"', "'").strip()

def flatten(items):
    for item in items or []:
        if isinstance(item, list):
            yield from flatten(item)
        elif isinstance(item, dict):
            yield item


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--m3u', type=Path, required=True)
    p.add_argument('--details', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--base-url', required=True)
    p.add_argument('--username', required=True)
    p.add_argument('--password', required=True)
    args = p.parse_args()
    base = args.base_url.rstrip('/')
    user, password = quote(args.username), quote(args.password)
    lines = args.m3u.read_text(errors='ignore').splitlines()
    existing = {line.split(',', 1)[-1].strip() for line in lines if line.startswith('#EXTINF:')}
    shows = 0; episodes = 0
    for raw in args.details.read_text(errors='ignore').splitlines():
        try: record = json.loads(raw)
        except json.JSONDecodeError: continue
        show = record.get('show') or {}; detail = record.get('detail') or {}
        show_name = safe(show.get('name'), f"Series {show.get('series_id', '')}")
        category = safe(show.get('category_name'), 'Uncategorised')
        logo = safe(show.get('cover'))
        added_show = False
        episodes_data = detail.get('episodes') or {}
        season_groups = episodes_data.items() if isinstance(episodes_data, dict) else [('1', episodes_data)]
        for season_key, season_items in season_groups:
            try: season = int(season_key)
            except (TypeError, ValueError): season = 1
            for index, episode in enumerate(flatten(season_items), 1):
                episode_id = episode.get('id')
                if not episode_id: continue
                try: number = int(episode.get('episode_num') or index)
                except (TypeError, ValueError): number = index
                title = safe(episode.get('title'), f'Episode {number}')
                label = f'{show_name} S{season:02d}E{number:02d} - {title}'
                if label in existing: continue
                ext = safe(episode.get('container_extension'), 'mp4')
                image = safe((episode.get('info') or {}).get('movie_image') or logo)
                group = f'VOD / TV Shows / {category} / {show_name} / Season {season:02d}'
                attrs = [f'tvg-name="{label}"', f'group-title="{group}"']
                if image: attrs.append(f'tvg-logo="{image}"')
                attrs.append(f'media-type="episode"')
                attrs.append(f'tv-show="{show_name}"')
                attrs.append(f'season="{season}"')
                attrs.append(f'episode="{number}"')
                lines.append('#EXTINF:-1 ' + ' '.join(attrs) + ',' + label)
                lines.append(f'{base}/series/{user}/{password}/{episode_id}.{ext}')
                existing.add(label); episodes += 1; added_show = True
        if added_show: shows += 1
    args.out.write_text('\n'.join(lines) + '\n')
    print(json.dumps({'shows_with_episodes': shows, 'episodes_added': episodes, 'output_bytes': args.out.stat().st_size}))

if __name__ == '__main__': main()
