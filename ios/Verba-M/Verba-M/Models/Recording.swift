import SwiftUI

struct Recording: Identifiable {
    let id = UUID()
    let title: String
    let date: String
    let duration: String
    let wordCount: String
    let speakers: Int
    let fileSize: String
    let iconColor: Color
    let isNew: Bool

    var participants: [String] {
        ["Sarah Chen", "Mike Torres", "Dana Park", "James Liu"]
    }

    var summaryPreview: String {
        "Product review meeting covering Q4 metrics, onboarding funnel analysis, and infrastructure migration timeline. Team agreed on a simplified onboarding approach and set a March deadline..."
    }
}

struct TranscriptEntry: Identifiable {
    let id = UUID()
    let timestamp: String
    let text: String
}

enum Classification: String, CaseIterable, Identifiable {
    case hipaa = "HIPAA"
    case ada = "ADA"
    case gina = "GINA"
    case fcra = "FCRA"

    var id: String { rawValue }
}

enum Sensitivity: String, CaseIterable, Identifiable {
    case confidential = "Confidential"
    case highlyConfidential = "Highly Confidential"
    case restricted = "Restricted"

    var id: String { rawValue }
}

extension Color {
    static let themeBg = Color(red: 0.059, green: 0.047, blue: 0.161)
    static let themeBgLight = Color(red: 0.102, green: 0.102, blue: 0.243)
    static let themePurple = Color(red: 0.4, green: 0.494, blue: 0.918)
    static let themeViolet = Color(red: 0.463, green: 0.294, blue: 0.635)
    static let themeGreen = Color(red: 0.18, green: 0.835, blue: 0.45)
    static let themeOrange = Color(red: 1.0, green: 0.647, blue: 0.012)
    static let themeRed = Color(red: 1.0, green: 0.278, blue: 0.341)
    static let themeBlue = Color(red: 0.118, green: 0.565, blue: 1.0)
    static let cardBg = Color.white.opacity(0.04)
    static let subtleText = Color.white.opacity(0.45)
    static let bodyText = Color.white.opacity(0.65)
    static let primaryText = Color.white.opacity(0.85)
}

let sampleRecordings: [Recording] = [
    Recording(title: "Product Review Meeting", date: "Jan 29, 2026", duration: "14:23", wordCount: "2,847", speakers: 4, fileSize: "12.4 MB", iconColor: .themePurple, isNew: true),
    Recording(title: "Sprint Retrospective", date: "Jan 27, 2026", duration: "32:10", wordCount: "5,102", speakers: 6, fileSize: "28.1 MB", iconColor: .themeGreen, isNew: false),
    Recording(title: "Client Onboarding Call", date: "Jan 24, 2026", duration: "45:07", wordCount: "8,340", speakers: 3, fileSize: "41.7 MB", iconColor: .themeOrange, isNew: false),
    Recording(title: "Design Review", date: "Jan 22, 2026", duration: "22:15", wordCount: "3,560", speakers: 5, fileSize: "18.3 MB", iconColor: .themePurple, isNew: false),
    Recording(title: "Weekly Standup Notes", date: "Jan 20, 2026", duration: "8:45", wordCount: "1,230", speakers: 8, fileSize: "6.2 MB", iconColor: .themeGreen, isNew: false),
]

let sampleTranscript: [TranscriptEntry] = [
    TranscriptEntry(timestamp: "00:00", text: "Good morning everyone. Thank you for joining today's product review meeting. I'd like to start by going over the agenda. We have three main topics to discuss today..."),
    TranscriptEntry(timestamp: "01:24", text: "First, let's look at the Q4 metrics. As you can see from the dashboard, our monthly active users increased by 18% compared to Q3. However, our customer retention rate dipped slightly to 72%..."),
    TranscriptEntry(timestamp: "03:45", text: "Sarah, could you walk us through the onboarding analysis? Sure. So we looked at the entire funnel and found that step three, where users connect their accounts, has a 23% drop-off rate..."),
    TranscriptEntry(timestamp: "06:12", text: "That's a significant insight. What are we proposing to fix that? We have two approaches. Option A is to simplify the step by making account connection optional. Option B is to add a guided tutorial..."),
]
