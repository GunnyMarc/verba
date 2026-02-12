import SwiftUI

struct ProcessingView: View {
    @State private var rotation: Double = 0

    let steps: [(label: String, state: StepState)] = [
        ("Audio uploaded successfully", .done),
        ("Full transcription complete", .done),
        ("Generating AI summary...", .active),
        ("Extracting key decisions", .pending),
        ("Identifying risks & next steps", .pending),
    ]

    enum StepState {
        case done, active, pending
    }

    var body: some View {
        ZStack {
            LinearGradient(colors: [.themeBg, .themeBgLight], startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer().frame(height: 60)

                Text("Analyzing Audio")
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.bottom, 8)

                Text("AI is processing your recording")
                    .font(.system(size: 14))
                    .foregroundColor(.white.opacity(0.5))
                    .padding(.bottom, 50)

                // Spinner
                ZStack {
                    Circle()
                        .stroke(Color.white.opacity(0.08), lineWidth: 4)
                        .frame(width: 140, height: 140)

                    Circle()
                        .trim(from: 0, to: 0.25)
                        .stroke(Color.themePurple, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                        .frame(width: 140, height: 140)
                        .rotationEffect(.degrees(rotation))

                    Text("🧠")
                        .font(.system(size: 36))
                }
                .padding(.bottom, 40)
                .onAppear {
                    withAnimation(.linear(duration: 1.2).repeatForever(autoreverses: false)) {
                        rotation = 360
                    }
                }

                // Steps
                VStack(spacing: 16) {
                    ForEach(Array(steps.enumerated()), id: \.offset) { index, step in
                        HStack(spacing: 14) {
                            ZStack {
                                Circle()
                                    .fill(stepColor(step.state))
                                    .frame(width: 28, height: 28)

                                switch step.state {
                                case .done:
                                    Image(systemName: "checkmark")
                                        .font(.system(size: 12, weight: .bold))
                                        .foregroundColor(.black)
                                case .active:
                                    Text("\(index + 1)")
                                        .font(.system(size: 14, weight: .bold))
                                        .foregroundColor(.white)
                                case .pending:
                                    Text("\(index + 1)")
                                        .font(.system(size: 14, weight: .bold))
                                        .foregroundColor(.white.opacity(0.3))
                                }
                            }

                            Text(step.label)
                                .font(.system(size: 14))
                                .foregroundColor(step.state == .pending ? .white.opacity(0.35) : .white.opacity(0.8))

                            Spacer()
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 14)
                        .background(Color.white.opacity(0.04))
                        .cornerRadius(14)
                    }
                }
                .padding(.horizontal, 24)

                Spacer()
            }
        }
    }

    private func stepColor(_ state: StepState) -> Color {
        switch state {
        case .done: return .themeGreen
        case .active: return .themePurple
        case .pending: return .white.opacity(0.1)
        }
    }
}
