# Xtream Playlist Manager

This repository maintains an IPTV playlist and includes a Kodi addon that turns the playlist into a clean media library. The addon separates **Live TV**, **Movies**, **TV Shows**, **Seasons**, and **Episodes** using M3U attributes, group names, and standard `S01E02` or `1x02` filename conventions.

## Playlist URL

The current public playlist is available at:

```text
https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u
```

## Kodi addon

The addon is located in [`plugin.video.xtreamplaylist`](plugin.video.xtreamplaylist). It provides a dark neon themed identity with branded icon and fanart, cached playlist loading, search, favourites, refresh, artwork support, playable stream items, and a browsing hierarchy for shows and seasons.

### Installation

Download [`build/plugin.video.xtreamplaylist-1.0.0.zip`](build/plugin.video.xtreamplaylist-1.0.0.zip), open Kodi, choose **Add-ons**, select **Install from zip file**, and open the downloaded ZIP. After installation, launch **Xtream Playlist Manager** and use the addon settings to change the M3U URL or cache duration.

The ZIP must retain the top-level `plugin.video.xtreamplaylist` directory. Kodi will use the default GitHub raw URL automatically when no custom URL is configured.

### Media organization

The addon recognizes movies when the group or stream metadata contains movie or film categories, or when a VOD file extension is present. It recognizes episodes from `S01E02` and `1x02` patterns, explicit series metadata, and `TV Shows` groups. Episodes are grouped by show and then season. Other entries appear under Live TV and retain their group metadata for filtering and sorting by the active Kodi skin.

The Kodi addon cannot change Kodi’s global skin, but it ships its own visual identity and uses Kodi’s native video list, artwork, information labels, favourites, context menus, and playback integration so it remains compatible with installed skins.

## Automatic playlist refresh

The GitHub Actions workflow can regenerate the playlist daily from Xtream credentials stored as repository secrets named `XTREAM_BASE_URL`, `XTREAM_USERNAME`, and `XTREAM_PASSWORD`. It now requests live streams, movies, and series episodes. Optional variables include `INCLUDE_MOVIES=0`, `INCLUDE_SERIES=0`, and `XTREAM_TIMEOUT`.

Because Xtream stream URLs normally contain account credentials, do not publish the generated playlist publicly unless that exposure is acceptable. A private repository or authenticated proxy is safer for sensitive accounts.

## Project structure

| Path | Purpose |
|---|---|
| `plugin.video.xtreamplaylist/` | Kodi addon source and artwork |
| `plugin.video.xtreamplaylist/default.py` | Playlist parser, classification, navigation, search, favourites, and playback |
| `scripts/generate_playlist.py` | Xtream-to-M3U exporter for live TV, movies, and episodes |
| `.github/workflows/update-playlist.yml` | Scheduled playlist refresh workflow |
| `build/plugin.video.xtreamplaylist-1.0.0.zip` | Kodi installation package |

The original project notes remain in [`README.legacy.md`](README.legacy.md).
