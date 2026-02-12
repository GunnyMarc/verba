import SwiftUI

struct SplashView: View {
    var onGetStarted: () -> Void

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.themeBg, Color(red: 0.188, green: 0.169, blue: 0.388), Color.themeBgLight],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Logo
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(colors: [.themePurple, .themeViolet], startPoint: .topLeading, endPoint: .bottomTrailing)
                        )
                        .frame(width: 120, height: 120)
                        .shadow(color: .themePurple.opacity(0.4), radius: 20, y: 10)

                    Image(systemName: "mic.fill")
                        .font(.system(size: 48))
                        .foregroundColor(.white)
                }
                .padding(.bottom, 28)

                Text("Verba-M")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.bottom, 8)

                Text("Record. Transcribe. Summarize.\nPowered by AI intelligence.")
                    .font(.system(size: 15))
                    .foregroundColor(.white.opacity(0.6))
                    .multilineTextAlignment(.center)
                    .lineSpacing(4)
                    .padding(.bottom, 48)

                Button(action: onGetStarted) {
                    Text("Get Started")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(width: 220, height: 52)
                        .background(
                            LinearGradient(colors: [.themePurple, .themeViolet], startPoint: .leading, endPoint: .trailing)
                        )
                        .cornerRadius(16)
                        .shadow(color: .themePurple.opacity(0.4), radius: 12, y: 8)
                }

                Spacer()
            }
        }
    }
}
