# XDREAM WebView app

This is a self-contained local `WKWebView` app source for iOS 15. It follows the structure of the open-source WebView sample at [approov/quickstart-ios-webkit-webview-urlsession](https://github.com/approov/quickstart-ios-webkit-webview-urlsession), which is MIT-licensed and demonstrates bundled local HTML with WKWebView. That repository is a source sample, not a ready-made IPA.

The page is bundled inside the app, so no public website is required. The token is entered into the page at runtime, held only in page memory, and cleared when the WebView is closed. The page reads the selected GitHub file, replaces only existing `/live/`, `/movie/`, and `/series/` Xtream URL credentials, and commits the modified file with its current SHA. It does not call the Xtream API and does not refresh or regenerate the playlist.

## Build an IPA

On a Mac, create a new iOS App project in Xcode named `XDREAM`, set the deployment target to iOS 15.0, replace the generated Swift app file with `XDREAMWebViewApp.swift`, add `WebAssets/index.html` to the app target, and build for a connected iPhone. Export the resulting unsigned or ad-hoc IPA according to the jailbreak signing tool you use, then install it on the jailbroken device.

A jailbroken device may allow an unsigned IPA, but it still needs a compiled arm64 executable and a valid `Info.plist`; HTML alone cannot be installed as an iOS app. This workspace does not contain Apple’s Xcode SDK, so it cannot emit the final IPA binary here.

## GitHub permissions

Use a fine-grained GitHub token restricted to `James1997s/xtream-playlist-manager` with **Contents: Read and write**. Do not embed the token in this source, the IPA, the `.deb`, or the repository.
