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
from xml.sax.saxutils import escape

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
            "logo": attrs.get("tvg-logo") or attrs.get("tvg-art") or attrs.get("logo", ""),
            "poster": attrs.get("poster") or attrs.get("cover") or attrs.get("tvg-logo", ""),
            "fanart": attrs.get("fanart") or attrs.get("tvg-fanart") or attrs.get("tvg-logo", ""),
            "group": attrs.get("group-title", "Live TV") or "Live TV",
            "kind": kind,
            "season": season,
            "episode": episode,
        })
        pending = None
    return entries


def load_entries(force=False):
    playlist_url = _setting("playlist_url", DEFAULT_PLAYLIST).strip()
    cache_minutes = int(_setting("cache_minutes", "60") or "60")
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
    fallback = ADDON.getAddonInfo("icon")
    art = {"thumb": logo or fallback, "icon": logo or fallback, "poster": info.get("poster") or logo or fallback, "fanart": info.get("fanart") or logo or fallback}
    li.setArt(art)
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


def _category(entry):
    """Return a stable, human-readable category for any playlist entry."""
    group = (entry.get("group") or "").strip()
    prefix = {"movie": "Movies / ", "episode": "TV Shows / "}.get(entry.get("kind"), "")
    if prefix and group.lower().startswith(prefix.lower()):
        group = group[len(prefix):].strip()
    return group or {"live": "Uncategorised", "movie": "Uncategorised", "episode": "Uncategorised"}.get(entry.get("kind"), "Uncategorised")


def _category_key(value):
    return (value or "").casefold()


def _slug(value):
    value = re.sub(r"[\\/:*?\"<>|]", "_", value or "Unknown")
    return re.sub(r"\s+", " ", value).strip(" .")[:180] or "Unknown"


def _native_root():
    path = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.xtreamplaylist/library")
    if not xbmcvfs.exists(path):
        xbmcvfs.mkdirs(path)
    return path


def _write_text(path, text):
    parent = os.path.dirname(path)
    if not xbmcvfs.exists(parent):
        xbmcvfs.mkdirs(parent)
    with xbmcvfs.File(path, "w") as handle:
        handle.write(text)


def _register_native_source(name, path):
    sources_path = xbmcvfs.translatePath("special://profile/sources.xml")
    try:
        import xml.etree.ElementTree as ET
        if xbmcvfs.exists(sources_path):
            with xbmcvfs.File(sources_path, "r") as handle:
                root_node = ET.fromstring(handle.read())
        else:
            root_node = ET.Element("sources")
        video = root_node.find("video")
        if video is None:
            video = ET.SubElement(root_node, "video")
        for source in video.findall("source"):
            if source.findtext("path") == path:
                return
        source = ET.SubElement(video, "source")
        ET.SubElement(source, "name").text = name
        ET.SubElement(source, "path", {"pathversion": "1"}).text = path
        ET.SubElement(source, "allowsharing").text = "false"
        xml = ET.tostring(root_node, encoding="unicode")
        _write_text(sources_path, "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n" + xml)
    except Exception as exc:
        xbmc.log("Could not register native Kodi source %s: %s" % (name, exc), xbmc.LOGWARNING)


def _art_tags(entry):
    thumb = escape(entry.get("poster") or entry.get("logo") or ADDON.getAddonInfo("icon"))
    fanart = escape(entry.get("fanart") or entry.get("poster") or entry.get("logo") or ADDON.getAddonInfo("icon"))
    return "<thumb aspect=\"poster\">%s</thumb><fanart><thumb>%s</thumb></fanart>" % (thumb, fanart)


def sync_native_library(entries):
    root_path = _native_root()
    movie_path = os.path.join(root_path, "movies")
    show_path = os.path.join(root_path, "tvshows")
    shows_written = set()
    for entry in entries:
        art = _art_tags(entry)
        if entry["kind"] == "movie":
            folder = os.path.join(movie_path, _slug(entry["name"]))
            stem = _slug(entry["name"])
            _write_text(os.path.join(folder, stem + ".strm"), entry["url"] + "\n")
            movie_xml = "<movie><title>%s</title><genre>%s</genre>%s</movie>" % (escape(entry["title"]), escape(entry["group"]), art)
            _write_text(os.path.join(folder, stem + ".nfo"), movie_xml)
        elif entry["kind"] == "episode":
            show_folder = os.path.join(show_path, _slug(entry["name"]))
            season_folder = os.path.join(show_folder, "Season %02d" % entry["season"])
            stem = "S%02dE%02d - %s" % (entry["season"], entry["episode"], _slug(entry["title"]))
            _write_text(os.path.join(season_folder, stem + ".strm"), entry["url"] + "\n")
            episode_xml = "<episodedetails><title>%s</title><showtitle>%s</showtitle><season>%d</season><episode>%d</episode>%s</episodedetails>" % (escape(entry["title"]), escape(entry["name"]), entry["season"], entry["episode"], art)
            _write_text(os.path.join(season_folder, stem + ".nfo"), episode_xml)
            if entry["name"] not in shows_written:
                show_xml = "<tvshow><title>%s</title>%s</tvshow>" % (escape(entry["name"]), art)
                _write_text(os.path.join(show_folder, "tvshow.nfo"), show_xml)
                shows_written.add(entry["name"])
    _register_native_source("Xtream Movies", "special://profile/addon_data/plugin.video.xtreamplaylist/library/movies/")
    _register_native_source("Xtream TV Shows", "special://profile/addon_data/plugin.video.xtreamplaylist/library/tvshows/")
    xbmc.executebuiltin("UpdateLibrary(video)")
    _notify("Native library sync complete")


def clear_native_library():
    root_path = _native_root()
    for subdir in ("movies", "tvshows"):
        path = os.path.join(root_path, subdir)
        if xbmcvfs.exists(path):
            xbmcvfs.delete(path)
    xbmc.executebuiltin("UpdateLibrary(video)")
    _notify("Synced library files cleared")


def setup_all(entries=None):
    if not xbmcgui.Dialog().yesno("Xtream Playlist Manager", "Set up the complete Kodi media experience now?", "This configures the playlist, native library sync, and Live TV setup."):
        return
    ADDON.openSettings()
    if _setting("native_library", "true").lower() == "true":
        sync_native_library(entries if entries is not None else load_entries(True))
    setup_native_tv()
    ADDON.setSetting("setup_complete", "true")


def setup_native_tv():
    playlist_url = _setting("playlist_url", DEFAULT_PLAYLIST)
    installed = xbmc.getCondVisibility("System.HasAddon(pvr.iptvsimple)")
    if installed:
        configured = False
        try:
            pvr = xbmcaddon.Addon("pvr.iptvsimple")
            pvr.setSetting("m3uPathType", "1")
            pvr.setSetting("m3uUrl", playlist_url)
            epg_url = _setting("epg_url", "")
            if epg_url:
                pvr.setSetting("epgPathType", "1")
                pvr.setSetting("epgUrl", epg_url)
            configured = True
        except Exception as exc:
            xbmc.log("PVR IPTV Simple auto-configuration unavailable: %s" % exc, xbmc.LOGWARNING)
        if configured:
            _notify("PVR M3U URL configured")
            xbmc.executebuiltin("PVR.RebuildDatabase")
            xbmc.executebuiltin("PVR.SetStarted(True)")
        message = "PVR IPTV Simple Client is installed.\n\nM3U URL:\n%s\n\nOpen PVR settings to verify channel and EPG options?" % playlist_url
        if xbmcgui.Dialog().yesno("Native Live TV setup", message):
            xbmc.executebuiltin("Addon.OpenSettings(pvr.iptvsimple)")
    else:
        message = "Kodi native TV needs PVR IPTV Simple Client.\n\nInstall and enable that addon, then run this setup again.\n\nM3U URL:\n%s" % playlist_url
        if xbmcgui.Dialog().yesno("Native Live TV setup", message, "Open Kodi's addon browser?"):
            xbmc.executebuiltin("ActivateWindow(addonbrowser)")


def root(entries):
    counts = defaultdict(int)
    for entry in entries:
        counts[entry["kind"]] += 1
    _item("Live TV  ·  %d channels" % counts["live"], _url("live"), True, ADDON.getAddonInfo("icon"))
    _item("Set up everything", _url("setup_all"), True, ADDON.getAddonInfo("icon"))
    _item("Set up native Live TV (PVR)", _url("setup_native_tv"), True, ADDON.getAddonInfo("icon"))
    _item("Movies  ·  %d titles" % counts["movie"], _url("movies"), True, ADDON.getAddonInfo("icon"))
    shows = len(set(e["name"] for e in entries if e["kind"] == "episode"))
    _item("TV Shows  ·  %d series" % shows, _url("shows"), True, ADDON.getAddonInfo("icon"))
    _item("Favourites", _url("favourites"), True, ADDON.getAddonInfo("icon"))
    _item("Search", _url("search"), True, ADDON.getAddonInfo("icon"))
    _item("Refresh playlist", _url("refresh"), True, ADDON.getAddonInfo("icon"))
    if _setting("native_library", "true").lower() == "true":
        _item("Sync to Kodi Movies / TV Shows", _url("sync_library"), True, ADDON.getAddonInfo("icon"))
        _item("Clear synced library files", _url("clear_library"), True, ADDON.getAddonInfo("icon"))
    _item("Settings", _url("settings"), True, ADDON.getAddonInfo("icon"))
    _finish()


def list_categories(entries, kind, title):
    """Show categories before titles so large playlists stay easy to browse."""
    grouped = defaultdict(list)
    for entry in entries:
        if entry["kind"] == kind:
            grouped[_category_key(_category(entry))].append(entry)
    for key in sorted(grouped, key=lambda value: value.casefold()):
        category = _category(grouped[key][0])
        label = "%s  ·  %d" % (category, len(grouped[key]))
        _item(label, _url("category", kind=kind, group=quote(category, safe="")), True, grouped[key][0].get("logo", ""), {"title": category, "genre": category})
    if not grouped:
        _notify("No %s found" % title.lower())
    _finish("videos")


def list_entries(entries, title, kind=None, group=None):
    selected = [e for e in entries if (not kind or e["kind"] == kind) and (not group or _category(e).casefold() == (group or "").casefold())]
    selected.sort(key=lambda e: (e["title"].casefold(), e["name"].casefold()))
    for entry in selected:
        category = _category(entry)
        info = {"title": entry["title"], "genre": category, "mediatype": "video", "poster": entry.get("poster", entry.get("logo", "")), "fanart": entry.get("fanart", entry.get("logo", ""))}
        _item(entry["title"], entry["url"], False, entry["logo"], info, _context(entry))
    if not selected:
        _notify("No matching items found")
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
        info = {"title": entry["title"], "tvshowtitle": show, "season": int(season), "episode": entry["episode"], "mediatype": "episode", "poster": entry.get("poster", entry.get("logo", "")), "fanart": entry.get("fanart", entry.get("logo", ""))}
        _item(label, entry["url"], False, entry["logo"], info, _context(entry))
    _finish("episodes")


def search(entries):
    term = xbmcgui.Dialog().input("Search channels, movies and TV shows", type=xbmcgui.INPUT_ALPHANUM)
    term = (term or "").strip()
    if not term:
        return root(entries)
    needle = term.casefold()
    matches = []
    for entry in entries:
        searchable = " ".join((entry.get("title", ""), entry.get("name", ""), _category(entry), entry.get("group", ""), entry.get("id", ""))).casefold()
        if needle in searchable:
            matches.append(entry)
    matches.sort(key=lambda e: ({"live": 0, "movie": 1, "episode": 2}.get(e["kind"], 9), e["title"].casefold()))
    if not matches:
        xbmcgui.Dialog().ok("Search", "No results found for: %s" % term)
        return root(entries)
    list_entries(matches, "Search: " + term)


def dispatch():
    params = dict(parse_qsl(urlparse(sys.argv[2] if len(sys.argv) > 2 else "").query))
    route = params.get("route", "root")
    if route == "setup_all":
        setup_all(load_entries())
        return
    if route == "settings":
        ADDON.openSettings()
        return
    if route == "setup_native_tv":
        setup_native_tv()
        return
    if route == "refresh":
        refreshed = load_entries(True)
        if _setting("native_library", "true").lower() == "true" and _setting("sync_on_refresh", "true").lower() == "true":
            sync_native_library(refreshed)
        _notify("Playlist refreshed")
        xbmc.executebuiltin("Container.Refresh")
        return
    if route == "sync_library":
        if _setting("native_library", "true").lower() == "true":
            sync_native_library(load_entries())
        else:
            _notify("Native library sync is disabled in Settings")
        return
    if route == "clear_library":
        if xbmcgui.Dialog().yesno("Xtream Playlist Manager", "Clear the synced Movies and TV Shows files?", "This does not delete your source playlist."):
            clear_native_library()
        return
    entries = load_entries()
    if route == "root" and _setting("setup_complete", "false").lower() != "true":
        if xbmcgui.Dialog().yesno("Welcome to Xtream Playlist Manager", "Run the complete setup wizard now?", "You can configure this later from the addon menu."):
            setup_all(entries)
            return
    if route == "root":
        root(entries)
    elif route == "live":
        list_categories(entries, "live", "Live TV")
    elif route == "movies":
        list_categories(entries, "movie", "Movies")
    elif route == "shows":
        list_categories(entries, "episode", "TV Shows")
    elif route == "category":
        list_entries(entries, "Category: " + _decode(params.get("group")), kind=params.get("kind"), group=_decode(params.get("group")))
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
