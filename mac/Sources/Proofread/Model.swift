import Foundation

struct Step: Identifiable {
    enum Kind { case tool(String), answer, prose }
    let id = UUID()
    let kind: Kind
    let title: String
    let detail: String
    let rejected: Bool

    init(log: String) {
        let text = log.trimmingCharacters(in: .whitespaces)
        if text.hasPrefix("prose:") {
            kind = .prose
            title = "thinking"
            detail = String(text.dropFirst(6)).trimmingCharacters(in: .whitespaces)
            rejected = false
        } else if text.hasPrefix("answer=") {
            kind = .answer
            title = "answer"
            detail = text
            rejected = text.hasSuffix("False")
        } else if let paren = text.firstIndex(of: "("), let arrow = text.range(of: "→") {
            let name = String(text[..<paren])
            let output = text[arrow.upperBound...].trimmingCharacters(in: .whitespaces)
            kind = .tool(name)
            title = name
            detail = "\(text[paren..<arrow.lowerBound].trimmingCharacters(in: .whitespaces))\n→ \(output)"
            rejected = output.hasPrefix("REJECTED")
        } else {
            kind = .prose
            title = "log"
            detail = text
            rejected = text.contains("REJECTED")
        }
    }
}

@MainActor
final class Solver: ObservableObject {
    @Published var steps: [Step] = []
    @Published var answer: String?
    @Published var verified = false
    @Published var running = false
    @Published var error: String?

    func solve(_ problem: String) async {
        steps = []; answer = nil; verified = false; error = nil; running = true
        defer { running = false }
        var request = URLRequest(url: URL(string: "http://localhost:8765/solve")!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 600
        request.httpBody = try? JSONEncoder().encode(["problem": problem])
        do {
            let (bytes, _) = try await URLSession.shared.bytes(for: request)
            for try await line in bytes.lines where line.hasPrefix("data: ") {
                guard let event = try? JSONSerialization.jsonObject(with: Data(line.dropFirst(6).utf8)) as? [String: Any] else { continue }
                switch event["type"] as? String {
                case "log": if let text = event["text"] as? String { steps.append(Step(log: text)) }
                case "done":
                    answer = (event["answer"] as? String) ?? (event["answer"].map { "\($0)" })
                    verified = event["verified"] as? Bool ?? false
                default: break
                }
            }
        } catch {
            self.error = error.localizedDescription
        }
    }
}
