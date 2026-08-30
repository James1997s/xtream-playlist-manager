# Xtream Playlist Manager — Stremio Addon

This is a proper Stremio HTTP addon that reads the project M3U playlist and exposes organised **Live TV**, **Movies**, and **TV Shows** catalogs. Live channels are labelled and sorted by **region**, **country**, playlist category, and language when those fields are available. Common prefixes such as `USA`, `UK`, `Canada`, `India`, `France`, and `Australia` are detected automatically, while explicit `country`, `tvg-country`, `language`, and `tvg-language` attributes take priority. Catalog search covers channel names, show names, categories, regions, countries, languages, and the `24/7` or `always-on` label. Live TV is split into **Regional Channels**, **24/7 Channels**, and **All Channels** catalogs. A channel is placed in the 24/7 catalog when its title, group, `tvg-name`, or `channel-type` contains markers such as `24/7`, `24 hours`, `always-on`, `continuous`, or `round-the-clock`. The playlist is refreshed automatically at most once per hour.

## Run locally

From this directory:

```bash
M3U_URL=https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u npm start
```

The manifest is then available at:

```text
http://localhost:7000/manifest.json
```

Stremio must be able to reach the server. For a local-only installation, use a tunnel or run the addon on a public HTTPS host. The addon server must remain online while Stremio uses it.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `7000` | HTTP listening port. |
| `M3U_URL` | The repository playlist URL | Source M3U playlist. |

## Install in Stremio

Open the public manifest URL in a browser, or paste it into Stremio’s **Addons → Add addon** field. For example:

```text
https://YOUR-HOST.example/manifest.json
```

The repository’s raw playlist URL is only the data source; it is **not** itself a Stremio addon URL.
