import SwiftUI

struct SummaryContentView: View {
    var body: some View {
        VStack(spacing: 14) {
            SummaryCard(
                icon: "doc.text",
                title: "Executive Summary",
                color: .themePurple,
                content: .text("Product review meeting covering Q4 metrics, onboarding funnel analysis, and infrastructure migration timeline. Team agreed on a simplified onboarding approach and set a March deadline for the cloud migration.")
            )

            SummaryCard(
                icon: "checkmark.circle",
                title: "Key Decisions Made",
                color: .themeGreen,
                content: .bullets([
                    "Adopt Option A: make account connection optional during onboarding",
                    "Allocate additional $50K budget for Q1 retention campaigns",
                    "Hire two senior engineers for the infrastructure team",
                ])
            )

            SummaryCard(
                icon: "gearshape",
                title: "Technical Discussion Points",
                color: .themeOrange,
                content: .bullets([
                    "Database migration from PostgreSQL to CockroachDB for horizontal scaling",
                    "API rate limiting needs to be implemented before v2.0 launch",
                    "OAuth 2.0 integration with new SSO provider (Okta)",
                ])
            )

            SummaryCard(
                icon: "exclamationmark.triangle",
                title: "Open Items & Risks",
                color: .themeRed,
                content: .bullets([
                    "Vendor contract for cloud hosting expires Feb 28 — renewal pending legal review",
                    "23% onboarding drop-off may worsen if not addressed by end of Q1",
                    "No fallback plan if CockroachDB migration encounters compatibility issues",
                ])
            )

            SummaryCard(
                icon: "arrow.right.circle",
                title: "Next Steps",
                color: .themeBlue,
                content: .bullets([
                    "Sarah to deliver onboarding redesign mockups by Feb 7",
                    "DevOps to complete staging environment for DB migration by Feb 14",
                    "Product team to finalize v2.0 feature list by Feb 10",
                    "Follow-up meeting scheduled for Feb 12 at 10:00 AM",
                ])
            )
        }
        .padding(.horizontal, 16)
        .padding(.bottom, 20)
    }
}

enum CardContent {
    case text(String)
    case bullets([String])
}

struct SummaryCard: View {
    let icon: String
    let title: String
    let color: Color
    let content: CardContent

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(color)
                Text(title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(color)
            }

            switch content {
            case .text(let str):
                Text(str)
                    .font(.system(size: 13))
                    .foregroundColor(.bodyText)
                    .lineSpacing(5)
            case .bullets(let items):
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(items, id: \.self) { item in
                        HStack(alignment: .top, spacing: 8) {
                            Text("•")
                                .foregroundColor(.white.opacity(0.3))
                            Text(item)
                                .font(.system(size: 13))
                                .foregroundColor(.bodyText)
                                .lineSpacing(4)
                        }
                    }
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.cardBg)
        .cornerRadius(16)
        .overlay(
            HStack {
                Rectangle()
                    .fill(color)
                    .frame(width: 3)
                Spacer()
            }
            .clipShape(RoundedRectangle(cornerRadius: 16))
        )
    }
}
