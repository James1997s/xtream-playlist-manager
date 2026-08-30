#!/usr/bin/env python3
"""Append Xtream VOD movies and series episodes to an existing M3U."""
from __future__ import annotations
import os
import sys
from urllib.parse import quote, urlparse, urlunparse
import requests


def required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise SystemExit(f'Missing required environment variable: {name}')
    return value


def base_url(raw):
    if not raw.startswith(('http://', 'https://')):
        raw = 'http://' + raw
    parsed = urlparse(raw.strip())
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), '', '', ''))


def safe(value, fallback=''):
    return str(value or fallback).replace('\n', ' ').replace('"', "'").strip()


def extinf(name, group, logo='', extra=''):
    attrs = [f'tvg-name="{safe(name)}"', f'group-title="{safe(group)}"']
    if logo:
        attrs.append(f'tvg-logo="{safe(logo)}"')
    if extra:
        attrs.append(extra)
    return '#EXTINF:-1 ' + ' '.join(attrs) + ',' + safe(name, 'Untitled')


def api(session, endpoint, username, password, action, timeout, **extra):
    params = {'username': username, 'password': password, 'action': action, **extra}
    response = session.get(endpoint, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def main():
    base = base_url(required('XTREAM_BASE_URL'))
    username, password = required('XTREAM_USERNAME'), required('XTREAM_PASSWORD')
    input_path = os.environ.get('INPUT_FILE', 'playlist.m3u')
    output_path = os.environ.get('OUTPUT_FILE', 'playlist-with-vod.m3u')
    timeout = int(os.environ.get('XTREAM_TIMEOUT', '45'))
    include_series = os.environ.get('INCLUDE_SERIES', '1') != '0'
    endpoint = base + '/player_api.php'
    user, secret = quote(username), quote(password)
    lines = open(input_path, encoding='utf-8', errors='ignore').read().splitlines()
    existing_ids = set()
    for line in lines:
        if line.startswith('#EXTINF:'):
            existing_ids.add(line.split(',', 1)[-1].strip())
    session = requests.Session()
    movies = api(session, endpoint, username, password, 'get_vod_streams', timeout)
    movie_count = 0
    episode_count = 0
    for item in movies if isinstance(movies, list) else []:
        stream_id = item.get('stream_id')
        if not stream_id:
            continue
        name = safe(item.get('name'), f'Movie {stream_id}')
        if name in existing_ids:
            continue
        ext = safe(item.get('container_extension'), 'mp4')
        group = 'VOD / Movies / ' + safe(item.get('category_name'), 'Uncategorised')
        lines.extend([extinf(name, group, safe(item.get('stream_icon')), 'media-type="movie"'), f'{base}/movie/{user}/{secret}/{stream_id}.{ext}'])
        existing_ids.add(name)
        movie_count += 1
    if include_series:
        shows = api(session, endpoint, username, password, 'get_series', timeout)
        for show in shows if isinstance(shows, list) else []:
            series_id = show.get('series_id')
            if not series_id:
                continue
            try:
                detail = api(session, endpoint, username, password, 'get_series_info', timeout, series_id=series_id)
            except requests.RequestException as exc:
                print(f'Skipping series {series_id}: {exc}', file=sys.stderr)
                continue
            show_name = safe(show.get('name'), f'Series {series_id}')
            group = 'VOD / TV Shows / ' + safe(show.get('category_name'), 'Uncategorised')
            logo = safe(show.get('cover'))
            episodes = detail.get('episodes', {}) if isinstance(detail, dict) else {}
            for season_key, season_items in episodes.items():
                try:
                    season = int(season_key)
                except (TypeError, ValueError):
                    season = 1
                for index, episode in enumerate(season_items or [], 1):
                    episode_id = episode.get('id')
                    if not episode_id:
                        continue
                    number = int(episode.get('episode_num') or index)
                    title = safe(episode.get('title'), f'Episode {number}')
                    ext = safe(episode.get('container_extension'), 'mp4')
                    label = f'{show_name} S{season:02d}E{number:02d} - {title}'
                    if label in existing_ids:
                        continue
                    image = safe((episode.get('info') or {}).get('movie_image') or logo)
                    extra = f'media-type="episode" tv-show="{safe(show_name)}" season="{season}" episode="{number}"'
                    lines.extend([extinf(label, group, image, extra), f'{base}/series/{user}/{secret}/{episode_id}.{ext}'])
                    existing_ids.add(label)
                    episode_count += 1
    with open(output_path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write('\n'.join(lines) + '\n')
    print(f'Wrote movies={movie_count}, episodes={episode_count} to {output_path}')


if __name__ == '__main__':
    try:
        main()
    except requests.RequestException as exc:
        print(f'Network/API error: {exc}', file=sys.stderr)
        raise SystemExit(1)
    except ValueError as exc:
        print(f'Invalid JSON from Xtream server: {exc}', file=sys.stderr)
        raise SystemExit(1)
