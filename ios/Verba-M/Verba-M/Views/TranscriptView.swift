import SwiftUI

struct TranscriptView: View {
    @Environment(\.dismiss) var dismiss
    @State private var selectedTab = 0
    @State private var showOptions = false

    var body: some View {
        ZStack {
            Color.themeBg.ignoresSafeArea()

            ScrollView {
                VStack(spacing: 0) {
                    // Nav bar
                    HStack(spacing: 12) {
                        Button(action: { dismiss() }) {
                            Circle()
                                .fill(Color.white.opacity(0.08))
                                .frame(width: 36, height: 36)
                                .overlay(
                                    Image(systemName: "arrow.left")
                                        .font(.system(size: 16))
                                        .foregroundColor(.white)
                                )
                        }

                        Text("Meeting Notes")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(.white)

                        Spacer()

                        Menu {
                            Button(action: {}) {
                                Label("Download", systemImage: "arrow.down.to.line")
                            }
                            Button(action: {}) {
                                Label("Share", systemImage: "square.and.arrow.up")
                            }
                        } label: {
                            Circle()
                                .fill(Color.white.opacity(0.08))
                                .frame(width: 36, height: 36)
                                .overlay(
                                    Image(systemName: "ellipsis")
                                        .font(.system(size: 16))
                                        .foregroundColor(.white)
                                )
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)

                    // Metadata
                    HStack(spacing: 16) {
                        Label("Jan 29, 2026", systemImage: "calendar")
                        Label("14:23", systemImage: "timer")
                        Label("2,847 words", systemImage: "doc.text")
                    }
                    .font(.system(size: 12))
                    .foregroundColor(.white.opacity(0.4))
                    .padding(.horizontal, 20)
                    .padding(.bottom, 16)

                    // Tabs
                    tabPicker

                    if selectedTab == 0 {
                        transcriptContent
                    } else {
                        SummaryContentView()
                    }
                }
            }
        }
        .navigationBarHidden(true)
    }

    private var tabPicker: some View {
        HStack(spacing: 0) {
            tabButton("Transcript", index: 0)
            tabButton("Summary", index: 1)
        }
        .padding(4)
        .background(Color.white.opacity(0.06))
        .cornerRadius(12)
        .padding(.horizontal, 20)
        .padding(.bottom, 16)
    }

    private func tabButton(_ title: String, index: Int) -> some View {
        Button(action: { withAnimation { selectedTab = index } }) {
            Text(title)
                .font(.system(size: 13, weight: selectedTab == index ? .semibold : .medium))
                .foregroundColor(selectedTab == index ? .white : .white.opacity(0.5))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(selectedTab == index ? Color.themePurple : Color.clear)
                .cornerRadius(10)
        }
    }

    private var transcriptContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            ForEach(sampleTranscript) { entry in
                HStack(alignment: .top, spacing: 0) {
                    Text(entry.timestamp)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.themePurple)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.themePurple.opacity(0.12))
                        .cornerRadius(6)
                        .padding(.trailing, 8)

                    Text(entry.text)
                        .font(.system(size: 14))
                        .foregroundColor(.white.opacity(0.75))
                        .lineSpacing(6)
                }
            }
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 20)
    }
}
