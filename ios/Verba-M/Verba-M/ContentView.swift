import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            SummariesListView()
                .tabItem {
                    Image(systemName: "square.grid.2x2")
                    Text("Home")
                }
                .tag(0)

            TranscriptView()
                .tabItem {
                    Image(systemName: "doc.text")
                    Text("Transcripts")
                }
                .tag(1)

            RecordingView()
                .tabItem {
                    Image(systemName: "mic.fill")
                    Text("Record")
                }
                .tag(2)

            SettingsPlaceholderView()
                .tabItem {
                    Image(systemName: "gearshape")
                    Text("Settings")
                }
                .tag(3)
        }
        .tint(.themePurple)
    }
}

struct SettingsPlaceholderView: View {
    var body: some View {
        ZStack {
            Color.themeBg.ignoresSafeArea()
            VStack(spacing: 16) {
                Image(systemName: "gearshape")
                    .font(.system(size: 48))
                    .foregroundColor(.white.opacity(0.3))
                Text("Settings")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(.white.opacity(0.5))
            }
        }
    }
}
