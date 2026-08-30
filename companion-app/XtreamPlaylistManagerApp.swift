import SwiftUI
import Security

@main
struct XtreamPlaylistManagerApp: App {
    var body: some Scene { WindowGroup { ContentView() } }
}

struct ContentView: View {
    @State private var owner = KeychainStore.string(for: "github.owner") ?? "James1997s"
    @State private var repo = KeychainStore.string(for: "github.repo") ?? "xtream-playlist-manager"
    @State private var branch = KeychainStore.string(for: "github.branch") ?? "main"
    @State private var path = KeychainStore.string(for: "github.path") ?? "playlist.m3u"
    @State private var token = KeychainStore.string(for: "github.token") ?? ""
    @State private var server = KeychainStore.string(for: "xtream.server") ?? ""
    @State private var username = KeychainStore.string(for: "xtream.username") ?? ""
    @State private var password = KeychainStore.string(for: "xtream.password") ?? ""
    @State private var status = "Enter the new Xtream details."
    @State private var isBusy = false

    var body: some View {
        NavigationView {
            Form {
                Section("GitHub file") {
                    TextField("Owner", text: $owner).autocapitalization(.none)
                    TextField("Repository", text: $repo).autocapitalization(.none)
                    TextField("Branch", text: $branch).autocapitalization(.none)
                    TextField("Playlist path", text: $path).autocapitalization(.none)
                    SecureField("GitHub token", text: $token)
                    Text("Use a fine-grained token limited to this repository with Contents: Read and write. It is stored only in Keychain.")
                        .font(.footnote).foregroundColor(.secondary)
                }
                Section("Xtream details") {
                    TextField("Server URL", text: $server)
                        .keyboardType(.URL).textContentType(.URL).autocapitalization(.none)
                    TextField("Username", text: $username)
                        .textContentType(.username).autocapitalization(.none)
                    SecureField("Password", text: $password).textContentType(.password)
                }
                Section {
                    Button(isBusy ? "Updating…" : "Update Xtream details") {
                        Task { await updateXtreamDetails() }
                    }.disabled(isBusy)
                    Button("Save details on this device") {
                        saveLocal(); status = "Saved locally in Keychain."
                    }.disabled(isBusy)
                }
                Section("Status") {
                    Text(status).font(.footnote)
                }
            }
            .navigationTitle("XDREAM")
        }
    }

    private func saveLocal() {
        KeychainStore.set(owner, for: "github.owner")
        KeychainStore.set(repo, for: "github.repo")
        KeychainStore.set(branch, for: "github.branch")
        KeychainStore.set(path, for: "github.path")
        KeychainStore.set(token, for: "github.token")
        KeychainStore.set(server, for: "xtream.server")
        KeychainStore.set(username, for: "xtream.username")
        KeychainStore.set(password, for: "xtream.password")
    }

    private func updateXtreamDetails() async {
        guard !owner.isEmpty, !repo.isEmpty, !branch.isEmpty, !path.isEmpty,
              !token.isEmpty, !server.isEmpty, !username.isEmpty, !password.isEmpty else {
            status = "Complete every field before updating."; return
        }
        saveLocal(); isBusy = true; defer { isBusy = false }
        do {
            let client = GitHubContentsClient(token: token)
            let current = try await client.read(owner: owner, repo: repo, path: path, ref: branch)
            let rewritten = try PlaylistRewriter.replaceXtreamDetails(
                in: current.content, server: server, username: username, password: password
            )
            guard rewritten.changed else {
                status = "No Xtream stream URLs were found to update."; return
            }
            try await client.write(owner: owner, repo: repo, path: path, branch: branch,
                                   content: rewritten.content, sha: current.sha,
                                   message: "Update Xtream details only")
            status = "Updated Xtream details in \\(rewritten.count) existing URL(s). No playlist refresh was performed."
        } catch {
            status = "Update failed: \(error.localizedDescription)"
        }
    }
}

struct PlaylistRewriteResult { let content: String; let count: Int; var changed: Bool { count > 0 } }

enum PlaylistRewriter {
    static func replaceXtreamDetails(in source: String, server: String, username: String, password: String) throws -> PlaylistRewriteResult {
        let base = try normalizedServer(server)
        let expression = try NSRegularExpression(pattern: "(?i)(https?://)[^/\\s]+/(live|movie|series)/[^/\\s]+/[^/\\s]+/")
        let replacement = "$1" + base.replacingOccurrences(of: "http://", with: "").replacingOccurrences(of: "https://", with: "") + "/$2/" + Self.urlSegment(username) + "/" + Self.urlSegment(password) + "/"
        var count = 0
        let range = NSRange(source.startIndex..<source.endIndex, in: source)
        let output = expression.stringByReplacingMatches(in: source, range: range, withTemplate: replacement)
        expression.enumerateMatches(in: source, range: range) { _, _, _ in count += 1 }
        return PlaylistRewriteResult(content: output, count: count)
    }

    private static func normalizedServer(_ value: String) throws -> String {
        var value = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if !value.hasPrefix("http://") && !value.hasPrefix("https://") { value = "http://" + value }
        guard let url = URL(string: value), let host = url.host, !host.isEmpty else { throw URLError(.badURL) }
        return url.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }

    private static func urlSegment(_ value: String) -> String {
        value.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? value
    }
}

struct GitHubFile { let content: String; let sha: String }

struct GitHubContentsClient {
    let token: String
    private var session: URLSession { URLSession(configuration: .ephemeral) }

    func read(owner: String, repo: String, path: String, ref: String) async throws -> GitHubFile {
        let url = try endpoint(owner: owner, repo: repo, path: path, query: [URLQueryItem(name: "ref", value: ref)])
        var request = URLRequest(url: url); request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization"); request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        let (data, response) = try await session.data(for: request); try validate(response)
        let decoded = try JSONDecoder().decode(GitHubContentResponse.self, from: data)
        guard let raw = Data(base64Encoded: decoded.content.replacingOccurrences(of: "\n", with: "")), let content = String(data: raw, encoding: .utf8) else { throw URLError(.cannotDecodeContentData) }
        return GitHubFile(content: content, sha: decoded.sha)
    }

    func write(owner: String, repo: String, path: String, branch: String, content: String, sha: String, message: String) async throws {
        let url = try endpoint(owner: owner, repo: repo, path: path, query: [])
        var request = URLRequest(url: url); request.httpMethod = "PUT"; request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization"); request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept"); request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(GitHubUpdate(message: message, content: Data(content.utf8).base64EncodedString(), sha: sha, branch: branch))
        let (_, response) = try await session.data(for: request); try validate(response)
    }

    private func endpoint(owner: String, repo: String, path: String, query: [URLQueryItem]) throws -> URL {
        var components = URLComponents(string: "https://api.github.com/repos/\(owner)/\(repo)/contents/\(path.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? path)")!
        components.queryItems = query; guard let url = components.url else { throw URLError(.badURL) }; return url
    }
    private func validate(_ response: URLResponse) throws { guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) } }
}

private struct GitHubContentResponse: Decodable { let content: String; let sha: String }
private struct GitHubUpdate: Encodable { let message: String; let content: String; let sha: String; let branch: String }

enum KeychainStore {
    static func set(_ value: String, for key: String) { let data = Data(value.utf8); let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key]; SecItemDelete(query as CFDictionary); SecItemAdd(query.merging([kSecValueData as String: data]) { _, new in new } as CFDictionary, nil) }
    static func string(for key: String) -> String? { let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key, kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]; var result: AnyObject?; guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess, let data = result as? Data else { return nil }; return String(data: data, encoding: .utf8) }
}
