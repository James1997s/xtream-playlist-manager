# WebView source research

The `paulirish/iOS-WebView-App` repository is a very old UIWebView debugging shell. Its own README says it is out of date and recommends newer projects, so it is not a good base for iOS 15.

The `geocolumbus/wkwebview` repository is also an old Swift 2/Xcode 7.2 sample from 2016. It is simpler and uses WKWebView, but it is not a ready-made IPA and still requires rebuilding with an Apple SDK. Source links: https://github.com/paulirish/iOS-WebView-App and https://github.com/geocolumbus/wkwebview

Conclusion: an existing GitHub WebView repository can provide source structure, but it will not remove the need for a compiled iOS executable. A jailbroken phone removes the App Store signing requirement; it does not turn HTML/JavaScript into a runnable app. The safest implementation is a locally bundled WKWebView page with native GitHub API calls or a carefully scoped bridge, with the token entered on-device and stored in Keychain.
