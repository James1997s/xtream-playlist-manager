import SwiftUI
import WebKit

@main
struct XDREAMWebViewApp: App {
    var body: some Scene { WindowGroup { WebViewScreen() } }
}

struct WebViewScreen: UIViewRepresentable {
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .nonPersistent()
        let view = WKWebView(frame: .zero, configuration: config)
        view.scrollView.contentInsetAdjustmentBehavior = .never
        if let url = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "WebAssets") {
            view.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        return view
    }
    func updateUIView(_ view: WKWebView, context: Context) {}
}

struct WebViewScreen_Previews: PreviewProvider {
    static var previews: some View { WebViewScreen() }
}
