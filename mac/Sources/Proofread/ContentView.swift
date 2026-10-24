import SwiftUI

private let examples = [
    "What is 5788^2?",
    "Solve x^2 - 5x + 6 = 0",
    "Integrate x*sin(x) dx",
    "Sum of primes below 100",
]

struct ContentView: View {
    @StateObject private var solver = Solver()
    @State private var problem = ""

    var body: some View {
        VStack(spacing: 20) {
            header
            inputField
            chips
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: 10) {
                        ForEach(solver.steps) { StepRow(step: $0) }
                        if let answer = solver.answer { AnswerCard(answer: answer, verified: solver.verified).id("answer") }
                        if let error = solver.error { Label(error, systemImage: "exclamationmark.triangle").foregroundStyle(.red) }
                    }
                    .padding(.horizontal, 4)
                    .animation(.spring(duration: 0.4), value: solver.steps.count)
                }
                .onChange(of: solver.steps.count) { withAnimation { proxy.scrollTo(solver.steps.last?.id) } }
                .onChange(of: solver.answer) { withAnimation { proxy.scrollTo("answer") } }
            }
        }
        .padding(28)
        .background(
            Color.black.opacity(0.35)
                .ignoresSafeArea()
        )
    }

    private var header: some View {
        HStack {
            Image(systemName: "checkmark.seal.fill").font(.largeTitle).foregroundStyle(.green)
            VStack(alignment: .leading) {
                Text("Proofread").font(.largeTitle.bold())
                Text("Math answers, verified step by step").foregroundStyle(.secondary)
            }
            Spacer()
            if solver.running { ProgressView().controlSize(.small) }
            Button("Clear", systemImage: "trash") { solver.steps = []; solver.answer = nil; solver.error = nil }
                .buttonStyle(.glass).disabled(solver.running)
        }
    }

    private var inputField: some View {
        HStack(spacing: 12) {
            TextField("Ask a math problem…", text: $problem)
                .textFieldStyle(.plain)
                .font(.title2)
                .onSubmit(submit)
            Button(action: submit) {
                Image(systemName: "arrow.up.circle.fill").font(.system(size: 30))
            }
            .buttonStyle(.plain)
            .foregroundStyle(problem.isEmpty ? .secondary : Color.accentColor)
            .disabled(problem.isEmpty || solver.running)
        }
        .padding(.horizontal, 22).padding(.vertical, 16)
        .glassEffect(.regular.interactive(), in: .rect(cornerRadius: 26))
    }

    private var chips: some View {
        GlassEffectContainer(spacing: 8) {
            HStack(spacing: 8) {
                ForEach(examples, id: \.self) { example in
                    Button(example) { problem = example; submit() }
                        .buttonStyle(.plain)
                        .font(.callout)
                        .padding(.horizontal, 14).padding(.vertical, 8)
                        .glassEffect(.regular.interactive(), in: .capsule)
                }
            }
        }
        .disabled(solver.running)
    }

    private func submit() {
        guard !problem.isEmpty, !solver.running else { return }
        Task { await solver.solve(problem) }
    }
}

struct StepRow: View {
    let step: Step

    private var badge: (String, Color) {
        switch step.kind {
        case .tool("sympy"): ("function", .purple)
        case .tool("check"): ("checkmark.circle", .blue)
        case .tool("recall"): ("brain", .orange)
        case .tool: ("wrench.and.screwdriver", .gray)
        case .answer: ("flag.checkered", .green)
        case .prose: ("text.bubble", .secondary)
        }
    }

    var body: some View {
        let (icon, color) = badge
        let tint = step.rejected ? Color.red : color
        HStack(alignment: .top, spacing: 12) {
            Label(step.title, systemImage: icon)
                .font(.caption.bold().monospaced())
                .padding(.horizontal, 10).padding(.vertical, 5)
                .background(tint.opacity(0.2), in: .capsule)
                .foregroundStyle(tint)
                .frame(width: 120, alignment: .leading)
            Text(step.detail)
                .font(.system(.callout, design: .monospaced))
                .foregroundStyle(step.rejected ? .red : .primary)
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(14)
        .glassEffect(.regular.tint(step.rejected ? .red.opacity(0.25) : .clear), in: .rect(cornerRadius: 16))
        .transition(.move(edge: .bottom).combined(with: .opacity))
    }
}

struct AnswerCard: View {
    let answer: String
    let verified: Bool

    var body: some View {
        let color: Color = verified ? .green : .orange
        VStack(spacing: 12) {
            Text(answer).font(.system(size: 48, weight: .bold, design: .rounded)).textSelection(.enabled)
            Label(verified ? "Verified by SymPy" : "Not verified", systemImage: verified ? "checkmark.seal.fill" : "questionmark.diamond")
                .font(.headline)
                .padding(.horizontal, 16).padding(.vertical, 8)
                .foregroundStyle(color)
                .glassEffect(.regular, in: .capsule)
        }
        .frame(maxWidth: .infinity)
        .padding(28)
        .glassEffect(.regular, in: .rect(cornerRadius: 28))
        .padding(.top, 8)
        .transition(.scale.combined(with: .opacity))
    }
}
