# Rootless packaging notes

The SwiftUI companion app is the user-facing application. To package it for a Dopamine rootless jailbreak, build the app archive with Xcode on macOS, then package the resulting `.app` under `/Applications/XtreamPlaylistManager.app` using Theos or a standard Debian packaging workflow.

A Linux environment cannot compile Apple SDK code or produce a signed iOS application, so this directory documents the final packaging target rather than pretending that a `.deb` was built here.

The package should target the rootless jailbreak layout and must not request unnecessary entitlements. Install through the user’s trusted package manager, then respring only if the packaging workflow requires it.
