# Xtream Playlist Manager Kodi Addon

This repository now ships one Kodi addon: **Xtream Playlist Manager**. It reads one M3U playlist URL from its own settings and organizes the entries inside the addon. It does not replace Kodi’s global skin, databases, accounts, or system configuration.

## Install

Download the Kodi addon ZIP:

```text
https://github.com/James1997s/xtream-playlist-manager/raw/main/build/plugin.video.xtreamplaylist-1.1.0.zip
```

In Kodi, open **Settings → Add-ons → Install from zip file**, select the ZIP, and then launch **Xtream Playlist Manager** from your video addons. If Kodi asks, enable **Unknown sources**.

## Configure the M3U

Open the addon context menu and choose **Settings**, or open **Add-ons → My add-ons → Video add-ons → Xtream Playlist Manager → Configure**. The default URL is:

```text
https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u
```

The available settings are the M3U playlist URL and cache duration in minutes. The addon downloads and caches the playlist, then refreshes it when the cache expires or when **Refresh playlist** is selected.

## Where media goes

| Playlist metadata | Addon location |
|---|---|
| Live channel or regular `.m3u8` entry | **Live TV** |
| `group-title` containing `Movie`, `Movies`, `Film`, or `Cinema`; `media-type="movie"`; or a VOD file extension | **Movies** |
| `S01E01` or `1x01` title pattern | **TV Shows → Show → Season → Episode** |
| `tv-show`, `series-name`, or an explicit TV-show group | **TV Shows → Show → Season → Episode** |
| Any saved channel or title | **Favourites** after choosing **Add to favourites** |

The addon cannot invent Movies or TV Shows that are absent from the M3U. If the playlist contains only live channels, the Movies and TV Shows sections will be empty. The Xtream generator in this repository can produce movie and episode metadata when the GitHub Actions workflow is configured with authorized Xtream credentials.

## Features

The addon provides artwork from `tvg-logo`, Kodi video metadata, playable stream items, category grouping, show/season/episode hierarchy, search, favourites, cached loading, and a manual refresh action. It uses the active Kodi skin, so it does not alter unrelated Kodi menus or settings.

## Security

Xtream stream URLs commonly contain account credentials. Do not publish a credential-bearing playlist publicly unless that exposure is acceptable. Use a private repository or an authenticated proxy when necessary.

## Development

The addon source is in [`plugin.video.xtreamplaylist`](plugin.video.xtreamplaylist). The current release is `1.1.0`. The earlier build-installer and skin experiments are retained in [`README.build-legacy.md`](README.build-legacy.md) for historical reference but are not part of the standalone addon package.

## Native Kodi library sync

Version `1.2.0` adds **Sync to Kodi Movies / TV Shows**. Enable **Enable native Movies and TV Shows library** in the addon settings, then select **Sync to Kodi Movies / TV Shows**. The addon creates Kodi-compatible STRM and NFO files, registers native video sources, writes show-level metadata, and triggers a video-library update. You can enable **Sync native library on refresh** to repeat this automatically after refreshing the M3U.

Artwork is loaded from `tvg-logo`, `tvg-art`, `poster`, `cover`, `fanart`, and `tvg-fanart` attributes when present. The addon passes poster, thumbnail, icon, and fanart artwork to Kodi list items and writes artwork tags into native movie, show, and episode NFO files. When the M3U has no artwork URL, the addon icon is used as a safe fallback.

After the first sync, open Kodi’s native **Movies** or **TV Shows** section and allow the library update to finish. Only entries that actually exist in the M3U can appear in the native library.
