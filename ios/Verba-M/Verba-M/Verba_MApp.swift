import SwiftUI

@main
struct Verba_MApp: App {
    @State private var hasCompletedOnboarding = false

    var body: some Scene {
        WindowGroup {
            if hasCompletedOnboarding {
                ContentView()
                    .preferredColorScheme(.dark)
            } else {
                SplashView(onGetStarted: {
                    withAnimation {
                        hasCompletedOnboarding = true
                    }
                })
                .preferredColorScheme(.dark)
            }
        }
    }
}
