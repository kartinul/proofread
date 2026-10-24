import SwiftUI
import WebKit

struct MathPreview: NSViewRepresentable {
    let tex: String

    func makeNSView(context: Context) -> WKWebView {
        let web = WKWebView()
        web.setValue(false, forKey: "drawsBackground")
        return web
    }

    func updateNSView(_ web: WKWebView, context: Context) {
        let json = String(data: try! JSONEncoder().encode(tex), encoding: .utf8)!
        web.loadHTMLString("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
        <meta name="color-scheme" content="light dark">
        <body style="margin:0;font:18px -apple-system;color:CanvasText">
        <div id="m"></div>
        <script>m.textContent = \(json); renderMathInElement(m, {delimiters: [{left: "$$", right: "$$", display: true}, {left: "$", right: "$", display: false}, {left: "\\\\(", right: "\\\\)", display: false}, {left: "\\\\[", right: "\\\\]", display: true}]})</script>
        """, baseURL: nil)
    }
}
