# XTPlaylist Companion rootless tweak

This is a **new** rootless jailbreak tweak for iOS 15. It is intentionally separate from the Swift companion app. The app edits the playlist through GitHub’s Contents API; the tweak is injected only into SpringBoard and records a load marker so package installation and activation can be verified without modifying third-party applications.

The companion app source is in `../companion-app/XtreamPlaylistManagerApp.swift`. It stores the GitHub token and Xtream details in Keychain, reads the selected M3U file, replaces only the credentials in `/live/`, `/movie/`, and `/series/` URL entries, and writes the updated file back with the existing blob SHA. It does not change channel names, groups, logos, or unrelated URLs.

## Build on macOS with Theos

A Linux system cannot link Apple SDK frameworks or sign an iOS application. On a Mac with Xcode and Theos installed:

```sh
cd rootless-tweak
make package FINALPACKAGE=1
```

The rootless package will be generated under `packages/` as an `iphoneos-arm64` Debian package. Build the companion Swift app in Xcode with a deployment target of iOS 15.0, sign it for the target device, and package the `.app` under `/Applications/XtreamPlaylistManager.app` if you want one installable Debian package containing both components.

## Install

Transfer the final `.deb` to the jailbroken iPhone and install it with Sileo, Zebra, or another rootless package manager. A SpringBoard reload may be requested after installation. The package must be installed only on a device you own or administer.

## GitHub token

Create a fine-grained GitHub token limited to this repository with **Contents: Read and write** permission. Do not put the token in the repository, an M3U file, a URL, or a screenshot. The app keeps it in the iOS Keychain.
