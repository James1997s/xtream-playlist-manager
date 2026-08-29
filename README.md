# Xtream Playlist Manager

This project contains a native iOS companion-app source file and a GitHub-hosted daily playlist updater. It is intended for **authorized Xtream/IPTV accounts only**.

## How it works

The iOS app stores the server URL, username, and password in the device Keychain. It can test the account and show a local M3U preview. GitHub Actions independently calls the Xtream API once per day and commits the resulting `playlist.m3u` file. The public playlist URL is:

```text
https://James1997s.github.io/xtream-playlist-manager/playlist.m3u
```

GitHub Pages must be enabled for the repository, using the `main` branch and the repository root as the source. The file can also be opened through the raw GitHub URL:

```text
https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u
```

## One-time GitHub setup

From a computer with the GitHub CLI installed and authenticated, run:

```bash
gh secret set XTREAM_BASE_URL --repo James1997s/xtream-playlist-manager
gh secret set XTREAM_USERNAME --repo James1997s/xtream-playlist-manager
gh secret set XTREAM_PASSWORD --repo James1997s/xtream-playlist-manager
```

Each command securely prompts for the value. Do not place credentials in this README, in the Swift source, or in a public issue. After setup, open **Actions → Update IPTV playlist → Run workflow** once to create the first file. The scheduled job then runs daily at 03:17 UTC.

## iOS companion app

`iOS/XtreamPlaylistManagerApp.swift` is a complete SwiftUI source file. Create a new iOS app project in Xcode, choose SwiftUI and Swift, set the deployment target to iOS 15.0 or later, replace the generated app source with this file, and build it for the jailbroken iPhone 7. A normal signed build may be installed through the user’s preferred sideloading method; a jailbreak package can be produced from the same source with Theos or an equivalent packaging workflow.

The app does not silently upload credentials to GitHub. This is intentional: a GitHub personal-access token inside an iPhone app could be extracted. Add the three repository secrets through GitHub’s authenticated interface or CLI instead.

## Important credential warning

Most Xtream M3U stream URLs embed the username and password because the IPTV player needs those values to authenticate. Therefore, a **public playlist can expose the account credentials** even though the GitHub Actions secrets are protected. Use a private/proxy playlist service if the provider does not allow credential-bearing public URLs or if you need to conceal the credentials.

## Limitations

This repository contains the working app source and automation files, but an actual `.deb` package cannot be compiled in this Linux environment because Apple’s SDK/Xcode toolchain and the target device signing environment are required. The project is structured so it can be opened and packaged on macOS with Xcode and Theos.
