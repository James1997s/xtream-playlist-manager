# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import time
import zipfile
from urllib.request import Request, urlopen

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
TITLE = "Xtream Build Installer"
BUILD_URL = "https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/build/xtream-kodi-build-1.0.0.zip"
MANIFEST_URL = "https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/build/xtream-kodi-build.json"


def home():
    return xbmcvfs.translatePath("special://home/")


def profile():
    path = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def download(url, destination, dialog):
    request = Request(url, headers={"User-Agent": "Xtream-Build-Installer/1.0"})
    with urlopen(request, timeout=60) as response, open(destination, "wb") as output:
        total = int(response.headers.get("Content-Length", "0") or 0)
        received = 0
        while True:
            block = response.read(1024 * 256)
            if not block:
                break
            output.write(block)
            received += len(block)
            if total:
                dialog.update(int(received * 100 / total), "Downloading Xtream Build", "%d%%" % int(received * 100 / total))


def safe_extract(archive, destination, full=False):
    destination = os.path.abspath(destination)
    allowed = ("addons/", "userdata/addon_data/plugin.video.xtreamplaylist/", "userdata/addon_data/plugin.program.xtreambuild/", "build-info.json")
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            name = member.filename.replace("\\", "/")
            if not full and not any(name.startswith(prefix) for prefix in allowed):
                continue
            target = os.path.abspath(os.path.join(destination, name))
            if not target.startswith(destination + os.sep):
                raise ValueError("Unsafe path in build archive")
            if member.is_dir():
                continue
            parent = os.path.dirname(target)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            with zf.open(member) as source, open(target, "wb") as output:
                output.write(source.read())


def backup_configuration():
    backup = os.path.join(profile(), "kodi-backup-%s.zip" % time.strftime("%Y%m%d-%H%M%S"))
    root = home()
    important = ["userdata/guisettings.xml", "userdata/profiles.xml", "userdata/addon_data", "addons"]
    with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative in important:
            source = os.path.join(root, relative)
            if os.path.isfile(source):
                archive.write(source, relative)
            elif os.path.isdir(source):
                for current, _, files in os.walk(source):
                    for filename in files:
                        full = os.path.join(current, filename)
                        archive.write(full, os.path.relpath(full, root))
    return backup


def restore_backup():
    files = [name for name in os.listdir(profile()) if name.startswith("kodi-backup-") and name.endswith(".zip")]
    if not files:
        xbmcgui.Dialog().ok(TITLE, "No Kodi backup was found on this device.")
        return
    files.sort(reverse=True)
    choice = xbmcgui.Dialog().select("Choose backup", files)
    if choice < 0:
        return
    archive = os.path.join(profile(), files[choice])
    try:
        safe_extract(archive, home(), full=True)
        if xbmcgui.Dialog().yesno(TITLE, "Backup restored.", "Restart Kodi now?"):
            xbmc.restart()
    except Exception as exc:
        xbmcgui.Dialog().ok(TITLE, "Restore failed.", str(exc))


def install(mode):
    dialog = xbmcgui.DialogProgress()
    dialog.create(TITLE, "Preparing %s installation" % mode)
    archive = os.path.join(profile(), "xtream-kodi-build.zip")
    try:
        if mode == "Full build":
            if not xbmcgui.Dialog().yesno(TITLE, "Full build installation changes Kodi layout, skin settings, menus, and bundled addon settings.", "A backup will be created first. Continue?"):
                return
            dialog.update(5, "Creating Kodi backup")
            backup = backup_configuration()
            xbmc.log("Created Kodi backup at %s" % backup, xbmc.LOGINFO)
        else:
            dialog.update(5, "Keeping your current Kodi configuration")
        download(BUILD_URL, archive, dialog)
        if dialog.iscanceled():
            return
        dialog.update(75, "Installing %s" % mode, "Applying Xtream addons and branding")
        safe_extract(archive, home(), full=(mode == "Full build"))
        dialog.update(100, "Installation complete", "Restart Kodi to apply changes")
        xbmc.sleep(700)
        if xbmcgui.Dialog().yesno(TITLE, "%s installed successfully." % mode, "Restart Kodi now?"):
            xbmc.restart()
    except Exception as exc:
        xbmc.log("Xtream build installation failed: %s" % exc, xbmc.LOGERROR)
        xbmcgui.Dialog().ok(TITLE, "Installation failed.", str(exc))
    finally:
        dialog.close()


def check_update():
    try:
        request = Request(MANIFEST_URL, headers={"User-Agent": "Xtream-Build-Installer/1.0"})
        with urlopen(request, timeout=20) as response:
            manifest = json.loads(response.read().decode("utf-8"))
        xbmcgui.Dialog().ok(TITLE, "Latest build: %s" % manifest.get("version", "unknown"), manifest.get("description", ""))
    except Exception as exc:
        xbmcgui.Dialog().ok(TITLE, "Could not check for updates.", str(exc))


def main():
    options = ["Safe install / update", "Full build install", "Restore Kodi backup", "Check latest build version", "Open project repository"]
    choice = xbmcgui.Dialog().select(TITLE, options)
    if choice == 0:
        install("Safe install")
    elif choice == 1:
        install("Full build")
    elif choice == 2:
        restore_backup()
    elif choice == 3:
        check_update()
    elif choice == 4:
        xbmc.executebuiltin("OpenURL(https://github.com/James1997s/xtream-playlist-manager)")


if __name__ == "__main__":
    main()
