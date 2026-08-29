import SwiftUI
import Security

@main
struct XtreamPlaylistManagerApp: App {
    var body: some Scene { WindowGroup { ContentView() } }
}

struct ContentView: View {
    @State private var baseURL = KeychainStore.string(for: "baseURL") ?? ""
    @State private var username = KeychainStore.string(for: "username") ?? ""
    @State private var password = KeychainStore.string(for: "password") ?? ""
    @State private var status = "Enter your Xtream details, then save them."
    @State private var isBusy = false
    @State private var generated = ""

    private let playlistURL = "https://James1997s.github.io/xtream-playlist-manager/playlist.m3u"

    var body: some View {
        NavigationView {
            Form {
                Section("Xtream connection") {
                    TextField("Server URL", text: $baseURL)
                        .keyboardType(.URL).textContentType(.URL).autocapitalization(.none)
                    TextField("Username", text: $username)
                        .textContentType(.username).autocapitalization(.none)
                    SecureField("Password", text: $password)
                        .textContentType(.password)
                }

                Section {
                    Button(isBusy ? "Checking…" : "Save and test connection") {
                        Task { await saveAndTest() }
                    }.disabled(isBusy)
                    Button("Generate local M3U preview") {
                        Task { await generatePreview() }
                    }.disabled(isBusy)
                }

                Section("Published playlist") {
                    Text(playlistURL).font(.footnote).textSelection(.enabled)
                    Button("Copy playlist URL") {
                        UIPasteboard.general.string = playlistURL
                        status = "Playlist URL copied."
                    }
                }

                Section("Status") {
                    Text(status).font(.footnote)
                    if !generated.isEmpty {
                        Text(generated).font(.system(.footnote, design: .monospaced))
                            .lineLimit(12).textSelection(.enabled)
                    }
                }
            }
            .navigationTitle("Xtream Playlist")
        }
    }

    private func normalizedURL() -> URL? {
        var value = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        if !value.hasPrefix("http://") && !value.hasPrefix("https://") { value = "http://" + value }
        return URL(string: value.trimmingCharacters(in: CharacterSet(charactersIn: "/")))
    }

    private func save() {
        KeychainStore.set(baseURL, for: "baseURL")
        KeychainStore.set(username, for: "username")
        KeychainStore.set(password, for: "password")
    }

    private func saveAndTest() async {
        guard let url = normalizedURL(), !username.isEmpty, !password.isEmpty else {
            status = "Please enter a valid server URL, username, and password."; return
        }
        save(); isBusy = true; defer { isBusy = false }
        var components = URLComponents(url: url.appendingPathComponent("player_api.php"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "username", value: username), URLQueryItem(name: "password", value: password)]
        do {
            let (data, response) = try await URLSession.shared.data(from: components!.url!)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
            _ = try JSONSerialization.jsonObject(with: data)
            status = "Saved securely on this device. Xtream connection is responding."
        } catch { status = "Connection failed: \(error.localizedDescription)" }
    }

    private func generatePreview() async {
        guard let url = normalizedURL() else { status = "Enter a valid server URL."; return }
        save(); isBusy = true; defer { isBusy = false }
        var components = URLComponents(url: url.appendingPathComponent("player_api.php"), resolvingAgainstBaseURL: false)
        components?.queryItems = [URLQueryItem(name: "username", value: username), URLQueryItem(name: "password", value: password), URLQueryItem(name: "action", value: "get_live_streams")]
        do {
            let (data, _) = try await URLSession.shared.data(from: components!.url!)
            let items = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] ?? []
            generated = "#EXTM3U\n" + items.prefix(10).compactMap { item in
                guard let id = item["stream_id"] else { return nil }
                return "#EXTINF:-1,\(item["name"] ?? "Channel")\n\(url)/live/\(username)/\(password)/\(id).m3u8"
            }.joined(separator: "\n")
            status = "Generated a preview with \(items.count) live streams."
        } catch { status = "Could not generate preview: \(error.localizedDescription)" }
    }
}

enum KeychainStore {
    static func set(_ value: String, for key: String) {
        let data = Data(value.utf8)
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key]
        SecItemDelete(query as CFDictionary)
        SecItemAdd((query.merging([kSecValueData as String: data]) { _, new in new }) as CFDictionary, nil)
    }
    static func string(for key: String) -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key, kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
}
