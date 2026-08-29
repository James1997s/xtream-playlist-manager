# -*- coding: utf-8 -*-
"""Xtream Playlist Manager Kodi plugin.

The plugin intentionally keeps the playlist as the source of truth and derives
movies, shows, seasons, and episodes from standard M3U attributes and filenames.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import re
import sys
import time
from collections import defaultdict
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
CACHE_FILE = os.path.join(PROFILE, "playlist-cache.json")
FAVOURITES_FILE = os.path.join(PROFILE, "favourites.json")
DEFAULT_PLAYLIST = "https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u"


def _ensure_profile():
    if not xbmcvfs.exists(PROFILE):
        xbmcvfs.mkdirs(PROFILE)


def _read_json(path, fallback):
    try:
        with xbmcvfs.File(path, "r") as handle:
            return json.loads(handle.read())
    except Exception:
        return fallback


def _write_json(path, value):
    _ensure_profile()
    with xbmcvfs.File(path, "w") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2))


def _setting(name, fallback=""):
    value = ADDON.getSetting(name)
    return value if value else fallback


def _notify(message, heading="Xtream Playlist Manager"):
    xbmcgui.Dialog().notification(heading, message, xbmcgui.NOTIFICATION_INFO, 3500)


def _decode(value):
    return unquote(value or "")


def _parse_attrs(header):
    attrs = {}
    for key, value in re.findall(r'([\w-]+)="([^"]*)"', header):
        attrs[key.lower()] = value.strip()
    return attrs


def _normalise_name(value):
    value = re.sub(r"\[[^\]]+\]|\([^)]*\)|\{[^}]*\}", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip(" .-_")
    return value or "Unknown"


def _classify(attrs, title, stream_url):
    text = " ".join([attrs.get("group-title", ""), attrs.get("category", ""), title, stream_url]).lower()
    episode = re.search(r"(?:^|[ ._-])s(\d{1,2})[ ._-]*e(\d{1,3})(?:$|[ ._-])", title.lower())
    episode_alt = re.search(r"(?:^|[ ._-])(\d{1,2})x(\d{1,3})(?:$|[ ._-])", title.lower())
    if episode or episode_alt or any(word in text for word in ("tv show", "tv shows", "series", "episodes")):
        match = episode or episode_alt
        season = int(match.group(1)) if match else 1
        number = int(match.group(2)) if match else 0
        clean_title = re.sub(r"[ ._-]*s\d{1,2}[ ._-]*e\d{1,3}", "", title, flags=re.I)
        clean_title = re.sub(r"[ ._-]*\d{1,2}x\d{1,3}", "", clean_title, flags=re.I).strip(" -")
        show_name = attrs.get("tv-show") or attrs.get("series-name") or _normalise_name(clean_title)
        return "episode", show_name, season, number
    if any(word in text for word in ("movie", "movies", "film", "films", "cinema")):
        return "movie", _normalise_name(title), 0, 0
    if re.search(r"\.(mkv|mp4|avi|mov)(\?|$)", stream_url, re.I):
        return "movie", _normalise_name(title), 0, 0
    return "live", _normalise_name(title), 0, 0


def parse_m3u(raw):
    entries = []
    pending = None
    for raw_line in raw.splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line:
            continue
        if line.upper().startswith("#EXTINF"):
            comma = line.find(",")
            header = line[:comma] if comma >= 0 else line
            title = line[comma + 1:].strip() if comma >= 0 else "Untitled"
            pending = (_parse_attrs(header), title)
            continue
        if line.startswith("#") or pending is None:
            continue
        attrs, title = pending
        kind, name, season, episode = _classify(attrs, title, line)
        entries.append({
            "id": attrs.get("tvg-id") or line,
            "title": title,
            "name": name,
            "url": line,
            "logo": attrs.get("tvg-logo", ""),
            "group": attrs.get("group-title", "Live TV") or "Live TV",
            "kind": kind,
            "season": season,
            "episode": episode,
        })
        pending = None
    return entries


def load_entries(force=False):
    playlist_url = _setting("playlist_url", DEFAULT_PLAYLIST).strip()
    cache_minutes = int(_setting("cache_minutes", "30") or "30")
    cached = _read_json(CACHE_FILE, {})
    now = int(time.time())
    if not force and cached.get("url") == playlist_url and now - int(cached.get("updated", 0)) < cache_minutes * 60:
        return cached.get("entries", [])
    try:
        request = Request(playlist_url, headers={"User-Agent": "Kodi Xtream Playlist Manager/1.0"})
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8", "replace")
        entries = parse_m3u(raw)
        _write_json(CACHE_FILE, {"url": playlist_url, "updated": now, "entries": entries})
        return entries
    except Exception as exc:
        xbmc.log("Playlist load failed: %s" % exc, xbmc.LOGERROR)
        if cached.get("entries"):
            _notify("Using the last cached playlist")
            return cached["entries"]
        xbmcgui.Dialog().ok("Playlist unavailable", "Could not load the playlist. Check the URL in Settings.")
        return []


def _url(route, **kwargs):
    query = {"route": route}
    query.update(kwargs)
    return BASE_URL + "?" + urlencode(query)


def _item(label, path, folder=False, logo="", info=None, context=None):
    info = info or {}
    li = xbmcgui.ListItem(label=label)
    li.setLabel2(info.get("label2", ""))
    if logo:
        li.setArt({"thumb": logo, "icon": logo, "poster": logo})
    li.setInfo("video", info)
    if context:
        li.addContextMenuItems(context)
    if not folder:
        li.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, path, li, isFolder=folder)


def _favourites():
    return set(_read_json(FAVOURITES_FILE, []))


def _toggle_favourite(entry):
    favourites = _favourites()
    key = entry["id"]
    if key in favourites:
        favourites.remove(key)
        _notify("Removed from favourites")
    else:
        favourites.add(key)
        _notify("Added to favourites")
    _write_json(FAVOURITES_FILE, sorted(favourites))


def _context(entry):
    label = "Remove from favourites" if entry["id"] in _favourites() else "Add to favourites"
    return [(label, "RunPlugin(%s)" % _url("toggle_favourite", entry_id=quote(entry["id"], safe="")))]


def _finish(content="videos", sort_method="label"):
    xbmcplugin.setContent(HANDLE, content)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)


def root(entries):
    counts = defaultdict(int)
    for entry in entries:
        counts[entry["kind"]] += 1
    _item("Live TV  ·  %d channels" % counts["live"], _url("live"), True, ADDON.getAddonInfo("icon"))
    _item("Movies  ·  %d titles" % counts["movie"], _url("movies"), True, ADDON.getAddonInfo("icon"))
    shows = len(set(e["name"] for e in entries if e["kind"] == "episode"))
    _item("TV Shows  ·  %d series" % shows, _url("shows"), True, ADDON.getAddonInfo("icon"))
    _item("Favourites", _url("favourites"), True, ADDON.getAddonInfo("icon"))
    _item("Search", _url("search"), True, ADDON.getAddonInfo("icon"))
    _item("Refresh playlist", _url("refresh"), True, ADDON.getAddonInfo("icon"))
    _item("Settings", _url("settings"), True, ADDON.getAddonInfo("icon"))
    _finish()


def list_entries(entries, title, kind=None, group=None):
    selected = [e for e in entries if (not kind or e["kind"] == kind) and (not group or e["group"] == group)]
    selected.sort(key=lambda e: e["title"].lower())
    for entry in selected:
        info = {"title": entry["title"], "genre": entry["group"], "mediatype": "video"}
        _item(entry["title"], entry["url"], False, entry["logo"], info, _context(entry))
    _finish()


def shows(entries):
    grouped = defaultdict(list)
    for entry in entries:
        if entry["kind"] == "episode":
            grouped[entry["name"]].append(entry)
    for name in sorted(grouped, key=str.lower):
        first = grouped[name][0]
        _item(name, _url("seasons", show=name), True, first["logo"], {"title": name, "mediatype": "tvshow"})
    _finish("tvshows")


def seasons(entries, show):
    grouped = defaultdict(list)
    for entry in entries:
        if entry["kind"] == "episode" and entry["name"] == show:
            grouped[entry["season"]].append(entry)
    for season in sorted(grouped):
        first = grouped[season][0]
        _item("Season %02d  ·  %d episodes" % (season, len(grouped[season])), _url("episodes", show=show, season=season), True, first["logo"], {"title": show, "season": season, "mediatype": "season"})
    _finish("seasons")


def episodes(entries, show, season):
    selected = [e for e in entries if e["kind"] == "episode" and e["name"] == show and e["season"] == int(season)]
    selected.sort(key=lambda e: (e["episode"], e["title"].lower()))
    for entry in selected:
        label = "E%02d  %s" % (entry["episode"], entry["title"]) if entry["episode"] else entry["title"]
        info = {"title": entry["title"], "tvshowtitle": show, "season": int(season), "episode": entry["episode"], "mediatype": "episode"}
        _item(label, entry["url"], False, entry["logo"], info, _context(entry))
    _finish("episodes")


def search(entries):
    term = xbmcgui.Dialog().input("Search playlist", type=xbmcgui.INPUT_ALPHANUM)
    if not term:
        return root(entries)
    needle = term.lower()
    matches = [e for e in entries if needle in (e["title"] + " " + e["name"] + " " + e["group"]).lower()]
    list_entries(matches, "Search: " + term)


def dispatch():
    params = dict(parse_qsl(urlparse(sys.argv[2] if len(sys.argv) > 2 else "").query))
    route = params.get("route", "root")
    if route == "settings":
        ADDON.openSettings()
        return
    if route == "refresh":
        load_entries(True)
        _notify("Playlist refreshed")
        xbmc.executebuiltin("Container.Refresh")
        return
    entries = load_entries()
    if route == "root":
        root(entries)
    elif route == "live":
        list_entries(entries, "Live TV", kind="live")
    elif route == "movies":
        list_entries(entries, "Movies", kind="movie")
    elif route == "shows":
        shows(entries)
    elif route == "seasons":
        seasons(entries, _decode(params.get("show")))
    elif route == "episodes":
        episodes(entries, _decode(params.get("show")), params.get("season", "1"))
    elif route == "favourites":
        favourites = _favourites()
        list_entries([e for e in entries if e["id"] in favourites], "Favourites")
    elif route == "search":
        search(entries)
    elif route == "toggle_favourite":
        entry_id = _decode(params.get("entry_id"))
        for entry in entries:
            if entry["id"] == entry_id:
                _toggle_favourite(entry)
                break
        xbmc.executebuiltin("Container.Refresh")
    else:
        root(entries)


if __name__ == "__main__":
    dispatch()
