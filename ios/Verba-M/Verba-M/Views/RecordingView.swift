import SwiftUI

struct RecordingView: View {
    @State private var isRecording = true
    @State private var elapsedSeconds: Int = 154 // 02:34
    @State private var waveformHeights: [CGFloat] = (0..<30).map { _ in CGFloat.random(in: 20...75) }
    @State private var timer: Timer?

    var body: some View {
        ZStack {
            LinearGradient(colors: [.themeBg, .themeBgLight], startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Text("Recording...")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.top, 30)
                    .padding(.bottom, 6)

                Text("Tap the stop button when finished")
                    .font(.system(size: 13))
                    .foregroundColor(.white.opacity(0.5))
                    .padding(.bottom, 40)

                // Waveform
                HStack(spacing: 3) {
                    ForEach(0..<30, id: \.self) { i in
                        RoundedRectangle(cornerRadius: 2)
                            .fill(
                                LinearGradient(colors: [.themePurple, .themeViolet], startPoint: .top, endPoint: .bottom)
                            )
                            .frame(width: 4, height: waveformHeights[i])
                    }
                }
                .frame(height: 80)
                .padding(.bottom, 20)

                // Timer
                Text(formatTime(elapsedSeconds))
                    .font(.system(size: 48, weight: .ultraLight))
                    .monospacedDigit()
                    .foregroundColor(.white)
                    .padding(.bottom, 8)

                Text("Meeting_2026-01-29.m4a")
                    .font(.system(size: 13))
                    .foregroundColor(.white.opacity(0.4))
                    .padding(.bottom, 50)

                // Controls
                HStack(spacing: 36) {
                    // Pause
                    Button(action: {}) {
                        Circle()
                            .fill(Color.white.opacity(0.1))
                            .frame(width: 56, height: 56)
                            .overlay(
                                Image(systemName: "pause.fill")
                                    .font(.system(size: 20))
                                    .foregroundColor(.white)
                            )
                    }

                    // Stop
                    Button(action: {}) {
                        Circle()
                            .fill(Color.themeRed)
                            .frame(width: 80, height: 80)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(Color.white)
                                    .frame(width: 28, height: 28)
                            )
                            .overlay(
                                Circle()
                                    .stroke(Color.themeRed.opacity(0.3), lineWidth: 5)
                                    .frame(width: 90, height: 90)
                            )
                            .shadow(color: .themeRed.opacity(0.5), radius: 15, y: 6)
                    }

                    // Bookmark
                    Button(action: {}) {
                        Circle()
                            .fill(Color.white.opacity(0.1))
                            .frame(width: 56, height: 56)
                            .overlay(
                                Image(systemName: "plus")
                                    .font(.system(size: 20))
                                    .foregroundColor(.white)
                            )
                    }
                }

                // Live transcription
                VStack(alignment: .leading, spacing: 8) {
                    Text("LIVE TRANSCRIPTION")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.themePurple)
                        .tracking(1)

                    HStack(spacing: 0) {
                        Text("...and so the key takeaway from this quarter is that we need to focus on improving our customer retention metrics. Sarah mentioned that the onboarding flow has a 23% drop-off rate at step three")
                            .font(.system(size: 14))
                            .foregroundColor(.white.opacity(0.7))
                            .lineSpacing(4)

                        Rectangle()
                            .fill(Color.themePurple)
                            .frame(width: 2, height: 16)
                            .opacity(isRecording ? 1 : 0)
                            .animation(.easeInOut(duration: 0.5).repeatForever(), value: isRecording)
                    }
                }
                .padding(16)
                .background(Color.white.opacity(0.05))
                .cornerRadius(16)
                .padding(.horizontal, 24)
                .padding(.top, 40)

                Spacer()
            }
        }
        .onAppear {
            startWaveformAnimation()
        }
        .onDisappear {
            timer?.invalidate()
        }
    }

    private func formatTime(_ seconds: Int) -> String {
        let m = seconds / 60
        let s = seconds % 60
        return String(format: "%02d:%02d", m, s)
    }

    private func startWaveformAnimation() {
        timer = Timer.scheduledTimer(withTimeInterval: 0.3, repeats: true) { _ in
            withAnimation(.easeInOut(duration: 0.3)) {
                waveformHeights = (0..<30).map { _ in CGFloat.random(in: 20...75) }
            }
        }
    }
}
