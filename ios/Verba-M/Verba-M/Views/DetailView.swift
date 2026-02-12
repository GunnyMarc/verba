import SwiftUI

struct DetailView: View {
    let recording: Recording
    @Environment(\.dismiss) var dismiss
    @State private var showOptions = false
    @State private var selectedClassifications: Set<String> = ["HIPAA"]
    @State private var selectedSensitivities: Set<String> = ["Confidential"]

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

                        Text("Details")
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
                            Divider()
                            Button(action: { showOptions = true }) {
                                Label("Classifications", systemImage: "tag")
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

                    // Title section
                    detailSection("Title") {
                        Text(recording.title)
                            .font(.system(size: 15))
                            .foregroundColor(.primaryText)
                    }

                    // Metadata rows
                    detailSection(nil) {
                        VStack(spacing: 0) {
                            detailRow("Date", recording.date)
                            detailRow("Duration", recording.duration)
                            detailRow("Word Count", recording.wordCount)
                            detailRow("Speakers", "\(recording.speakers) detected")
                            detailRow("File Size", recording.fileSize, isLast: true)
                        }
                    }

                    // Applied classifications
                    detailSection("Applied Classifications") {
                        HStack(spacing: 8) {
                            ForEach(Array(selectedClassifications.sorted()), id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 12, weight: .semibold))
                                    .foregroundColor(.themePurple)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 5)
                                    .background(Color.themePurple.opacity(0.2))
                                    .cornerRadius(8)
                            }
                            ForEach(Array(selectedSensitivities.sorted()), id: \.self) { tag in
                                Text(tag)
                                    .font(.system(size: 12, weight: .semibold))
                                    .foregroundColor(.themePurple)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 5)
                                    .background(Color.themePurple.opacity(0.2))
                                    .cornerRadius(8)
                            }
                        }
                    }

                    // Participants
                    detailSection("Participants") {
                        Text(recording.participants.joined(separator: " · "))
                            .font(.system(size: 14))
                            .foregroundColor(.primaryText)
                            .lineSpacing(6)
                    }

                    // Summary preview
                    detailSection("Summary Preview") {
                        Text(recording.summaryPreview)
                            .font(.system(size: 13))
                            .foregroundColor(.white.opacity(0.6))
                            .lineSpacing(5)
                    }
                }
                .padding(.bottom, 100)
            }
        }
        .navigationBarHidden(true)
        .sheet(isPresented: $showOptions) {
            OptionsSheet(
                selectedClassifications: $selectedClassifications,
                selectedSensitivities: $selectedSensitivities
            )
            .presentationDetents([.medium])
            .presentationDragIndicator(.visible)
        }
    }

    private func detailSection(_ label: String?, @ViewBuilder content: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            if let label = label {
                Text(label.uppercased())
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white.opacity(0.35))
                    .tracking(1)
            }
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color.cardBg)
        .cornerRadius(14)
        .padding(.horizontal, 20)
        .padding(.bottom, 14)
    }

    private func detailRow(_ label: String, _ value: String, isLast: Bool = false) -> some View {
        VStack(spacing: 0) {
            HStack {
                Text(label)
                    .font(.system(size: 14))
                    .foregroundColor(.subtleText)
                Spacer()
                Text(value)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.primaryText)
            }
            .padding(.vertical, 10)

            if !isLast {
                Divider()
                    .background(Color.white.opacity(0.05))
            }
        }
    }
}

struct OptionsSheet: View {
    @Binding var selectedClassifications: Set<String>
    @Binding var selectedSensitivities: Set<String>
    @Environment(\.dismiss) var dismiss

    var body: some View {
        ZStack {
            Color(red: 0.165, green: 0.153, blue: 0.329).ignoresSafeArea()

            VStack(alignment: .leading, spacing: 0) {
                Text("Options")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    .padding(.bottom, 16)

                // Classification header
                Text("CLASSIFICATION")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white.opacity(0.35))
                    .tracking(1)
                    .padding(.horizontal, 20)
                    .padding(.bottom, 8)

                ForEach(Classification.allCases) { cls in
                    checkRow(cls.rawValue, isSelected: selectedClassifications.contains(cls.rawValue)) {
                        toggleSet(&selectedClassifications, cls.rawValue)
                    }
                }

                Divider()
                    .background(Color.white.opacity(0.08))
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)

                // Sensitivity header
                Text("SENSITIVITY")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white.opacity(0.35))
                    .tracking(1)
                    .padding(.horizontal, 20)
                    .padding(.bottom, 8)

                ForEach(Sensitivity.allCases) { sens in
                    checkRow(sens.rawValue, isSelected: selectedSensitivities.contains(sens.rawValue)) {
                        toggleSet(&selectedSensitivities, sens.rawValue)
                    }
                }

                Spacer()
            }
        }
    }

    private func checkRow(_ label: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 12) {
                ZStack {
                    RoundedRectangle(cornerRadius: 5)
                        .fill(isSelected ? Color.themePurple : Color.clear)
                        .frame(width: 22, height: 22)
                        .overlay(
                            RoundedRectangle(cornerRadius: 5)
                                .stroke(isSelected ? Color.themePurple : Color.white.opacity(0.25), lineWidth: 2)
                        )

                    if isSelected {
                        Image(systemName: "checkmark")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white)
                    }
                }

                Text(label)
                    .font(.system(size: 15))
                    .foregroundColor(.white)

                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
        }
    }

    private func toggleSet(_ set: inout Set<String>, _ value: String) {
        if set.contains(value) {
            set.remove(value)
        } else {
            set.insert(value)
        }
    }
}
