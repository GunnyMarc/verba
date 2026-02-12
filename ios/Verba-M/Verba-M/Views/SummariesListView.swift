import SwiftUI

struct SummariesListView: View {
    @State private var searchText = ""

    var filteredRecordings: [Recording] {
        if searchText.isEmpty { return sampleRecordings }
        return sampleRecordings.filter { $0.title.localizedCaseInsensitiveContains(searchText) }
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.themeBg.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 0) {
                        // Header
                        Text("Summaries")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 20)
                            .padding(.top, 16)
                            .padding(.bottom, 8)

                        // Search
                        HStack(spacing: 10) {
                            Image(systemName: "magnifyingglass")
                                .foregroundColor(.white.opacity(0.3))
                            TextField("Search summaries...", text: $searchText)
                                .foregroundColor(.white)
                                .font(.system(size: 15))
                        }
                        .padding(12)
                        .background(Color.white.opacity(0.06))
                        .cornerRadius(12)
                        .padding(.horizontal, 20)
                        .padding(.bottom, 12)

                        // List
                        ForEach(filteredRecordings) { recording in
                            RecordingRow(recording: recording)
                                .padding(.horizontal, 20)
                                .padding(.vertical, 4)
                        }
                    }
                    .padding(.bottom, 100)
                }
            }
            .navigationBarHidden(true)
        }
    }
}

struct RecordingRow: View {
    let recording: Recording

    var body: some View {
        HStack(spacing: 14) {
            // Icon
            RoundedRectangle(cornerRadius: 12)
                .fill(recording.iconColor.opacity(0.15))
                .frame(width: 44, height: 44)
                .overlay(
                    Image(systemName: "mic.fill")
                        .font(.system(size: 18))
                        .foregroundColor(recording.iconColor)
                )

            // Content
            VStack(alignment: .leading, spacing: 4) {
                Text(recording.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)
                Text("\(recording.date) · \(recording.duration) · \(recording.wordCount) words")
                    .font(.system(size: 12))
                    .foregroundColor(.white.opacity(0.35))
            }

            Spacer()

            // Details button
            NavigationLink(destination: DetailView(recording: recording)) {
                Text("Details")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.themePurple)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(Color.themePurple.opacity(0.12))
                    .cornerRadius(10)
            }

            // New badge
            if recording.isNew {
                Text("New")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.themePurple)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.themePurple.opacity(0.15))
                    .cornerRadius(8)
            }
        }
        .padding(16)
        .background(Color.cardBg)
        .cornerRadius(16)
    }
}
