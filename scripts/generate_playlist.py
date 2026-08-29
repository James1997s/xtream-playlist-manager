#!/usr/bin/env python3
"""Generate a multi-section Xtream M3U playlist for Kodi."""
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


def clean_base(raw):
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


def get(session, api, username, password, action, timeout, **extra):
    params = {'username': username, 'password': password, 'action': action}
    params.update(extra)
    response = session.get(api, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def main():
    base = clean_base(required('XTREAM_BASE_URL'))
    username, password = required('XTREAM_USERNAME'), required('XTREAM_PASSWORD')
    timeout = int(os.environ.get('XTREAM_TIMEOUT', '30'))
    output = os.environ.get('OUTPUT_FILE', 'playlist.m3u')
    session = requests.Session()
    api = base + '/player_api.php'
    user, secret = quote(username), quote(password)
    lines = ['#EXTM3U', '# Generated from Xtream API; includes live TV, movies, and TV episodes']
    totals = {'live': 0, 'movies': 0, 'episodes': 0}

    for item in get(session, api, username, password, 'get_live_streams', timeout):
        stream_id = item.get('stream_id')
        if not stream_id:
            continue
        name = safe(item.get('name'), f'Channel {stream_id}')
        lines += [extinf(name, safe(item.get('category_name'), 'Live TV'), safe(item.get('stream_icon'))), f'{base}/live/{user}/{secret}/{stream_id}.m3u8']
        totals['live'] += 1

    if os.environ.get('INCLUDE_MOVIES', '1') != '0':
        for item in get(session, api, username, password, 'get_vod_streams', timeout):
            stream_id = item.get('stream_id')
            if not stream_id:
                continue
            name = safe(item.get('name'), f'Movie {stream_id}')
            ext = safe(item.get('container_extension'), 'mp4')
            group = 'Movies / ' + safe(item.get('category_name'), 'Uncategorised')
            lines += [extinf(name, group, safe(item.get('stream_icon')), 'media-type="movie"'), f'{base}/movie/{user}/{secret}/{stream_id}.{ext}']
            totals['movies'] += 1

    if os.environ.get('INCLUDE_SERIES', '1') != '0':
        for show in get(session, api, username, password, 'get_series', timeout):
            series_id = show.get('series_id')
            if not series_id:
                continue
            try:
                detail = get(session, api, username, password, 'get_series_info', timeout, series_id=series_id)
            except requests.RequestException as exc:
                print(f'Skipping series {series_id}: {exc}', file=sys.stderr)
                continue
            show_name = safe(show.get('name'), f'Series {series_id}')
            group = 'TV Shows / ' + safe(show.get('category_name'), 'Uncategorised')
            logo = safe(show.get('cover'))
            for season_key, season_items in (detail.get('episodes', {}) if isinstance(detail, dict) else {}).items():
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
                    image = safe((episode.get('info') or {}).get('movie_image') or logo)
                    attrs = f'media-type="episode" tv-show="{safe(show_name)}" season="{season}" episode="{number}"'
                    lines += [extinf(label, group, image, attrs), f'{base}/series/{user}/{secret}/{episode_id}.{ext}']
                    totals['episodes'] += 1

    with open(output, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('Wrote live={live}, movies={movies}, episodes={episodes} to {output}'.format(output=output, **totals))


if __name__ == '__main__':
    try:
        main()
    except requests.RequestException as exc:
        print(f'Network/API error: {exc}', file=sys.stderr)
        raise SystemExit(1)
    except ValueError as exc:
        print(f'Invalid JSON from Xtream server: {exc}', file=sys.stderr)
        raise SystemExit(1)
