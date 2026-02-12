# Verba-M - iOS Mobile Application

Verba-M is the iOS companion app for the Verba media processing suite. Built with SwiftUI, it provides a native mobile experience for recording, transcribing, and summarizing audio content on iPhone and iPad.

## Overview

Verba-M is a SwiftUI-based iOS application that enables users to:
- **Record audio** with live waveform visualization and real-time transcription
- **View and manage transcripts** with timestamped entries
- **Generate AI summaries** of recordings with key decisions, technical points, risks, and action items
- **Organize recordings** with search, classifications, and metadata
- **Export and share** transcripts and summaries

## Project Structure

```
ios/
└── Verba-M/
    ├── Verba-M.xcodeproj/         # Xcode project configuration
    └── Verba-M/                   # Application source code
        ├── Verba_MApp.swift       # App entry point
        ├── ContentView.swift       # Main tab navigation
        ├── Models/
        │   └── Recording.swift     # Data models and theme colors
        ├── Views/
        │   ├── SplashView.swift    # Onboarding screen
        │   ├── RecordingView.swift # Audio recording interface
        │   ├── SummariesListView.swift # Home screen with recordings list
        │   ├── TranscriptView.swift    # Transcript viewer with tabs
        │   ├── SummaryView.swift       # AI-generated summary cards
        │   ├── DetailView.swift        # Recording metadata and details
        │   └── ProcessingView.swift    # AI processing status screen
        └── Assets.xcassets/        # App icon and asset catalog
```

## Features

### 1. Splash Screen
- **Gradient background** with app branding
- **App name**: Verba-M (renamed from Jiminy)
- **Tagline**: "Record. Transcribe. Summarize. Powered by AI intelligence."
- **Get Started button** to enter the main app

### 2. Recording Interface
- **Live waveform visualization** with animated bars
- **Timer** displaying elapsed recording time
- **Pause and Stop controls** with visual feedback
- **Bookmark button** for marking important moments
- **Live transcription preview** with blinking cursor animation

### 3. Summaries List (Home)
- **Grid view** of all recordings
- **Search functionality** to filter by title
- **Recording cards** with:
  - Icon with custom color
  - Title, date, duration, word count
  - "New" badge for recent recordings
  - "Details" button for navigation
- **Dark theme UI** matching the Verba brand

### 4. Transcript Viewer
- **Tabbed interface** switching between Transcript and Summary views
- **Timestamped entries** with color-coded badges
- **Metadata display**: date, duration, word count
- **Menu options**: Download, Share

### 5. AI Summary View
- **Structured summary cards** including:
  - Executive Summary
  - Key Decisions Made
  - Technical Discussion Points
  - Open Items & Risks
  - Next Steps
- **Color-coded sections** with icons
  - Purple: Executive summary
  - Green: Decisions
  - Orange: Technical  
  - Red: Risks
  - Blue: Action items

### 6. Detail View
- **Full metadata** display
- **Applied classifications** (HIPAA, ADA, GINA, FCRA)
- **Sensitivity levels** (Confidential, Highly Confidential, Restricted)
- **Participants list**
- **Summary preview**
- **Options sheet** for managing tags and classifications

### 7. Processing View
- **Animated spinner** during AI analysis
- **Step-by-step progress** indicators:
  - Audio uploaded
  - Transcription complete
  - Generating summary
  - Extracting key decisions
  - Identifying risks & next steps
- **Color-coded status**: Green (done), Purple (active), Gray (pending)

## Tech Stack

- **Language**: Swift
- **Framework**: SwiftUI
- **Minimum iOS Version**: iOS 16.0+
- **Architecture**: MVVM with declarative UI
- **Theme**: Dark mode with custom purple/violet gradient accent colors

## Design System

### Color Palette

```swift
static let themeBg = Color(red: 0.059, green: 0.047, blue: 0.161)          // #0F0C29 - Dark background
static let themeBgLight = Color(red: 0.102, green: 0.102, blue: 0.243)     // #1A1A3E - Lighter background
static let themePurple = Color(red: 0.4, green: 0.494, blue: 0.918)        // #667EEA - Primary accent
static let themeViolet = Color(red: 0.463, green: 0.294, blue: 0.635)      // #764BA2 - Secondary accent
static let themeGreen = Color(red: 0.18, green: 0.835, blue: 0.45)         // #2ED573 - Success
static let themeOrange = Color(red: 1.0, green: 0.647, blue: 0.012)        // #FFA503 - Warning
static let themeRed = Color(red: 1.0, green: 0.278, blue: 0.341)           // #FF4757 - Error/Stop
static let themeBlue = Color(red: 0.118, green: 0.565, blue: 1.0)          // #1E90FF - Info
```

### Typography

- **Titles**: System font, 28-32pt, bold
- **Headings**: System font, 18-22pt, semibold
- **Body**: System font, 13-15pt, regular
- **Captions**: System font, 11-12pt, medium
- **Timestamps**: System font, 11pt, semibold, monospacedDigit

## Building and Running

### Prerequisites

- **Xcode 15.0+** (for iOS 17 SDK)
- **macOS Ventura 13.0+** or later
- **Apple Developer Account** (for device testing)

### Build Steps

1. Open the project:
   ```bash
   open ios/Verba-M/Verba-M.xcodeproj
   ```

2. Select a target device or simulator in Xcode

3. Build and run: `Cmd + R`

### Project Configuration

The app uses a standard iOS app configuration with:
- **Bundle Identifier**: `com.verba.verba-m` (configure in Xcode)
- **Deployment Target**: iOS 16.0
- **Supported Devices**: iPhone, iPad
- **Orientations**: Portrait, Landscape

## Integration with Verba Backend

**Note**: This is currently a UI mockup app with sample data. To integrate with the Verba backend:

1. **Add networking layer** using `URLSession` or Alamofire
2. **Connect to FastAPI backend** at `https://localhost:30319`
3. **Implement API calls** for:
   - Audio upload and transcription
   - Summary generation
   - Recording metadata storage
4. **Add authentication** using API keys from Settings
5. **Handle SSE streams** for real-time progress updates
6. **Implement local storage** using CoreData or SwiftData for offline access

## Sample Data

The app currently includes hardcoded sample data for demonstration:
- 5 sample recordings with realistic metadata
- Sample transcript entries with timestamps
- Sample summary cards with structured content

## Next Steps

To make this a production-ready app:

1. **Backend Integration**
   - [ ] Implement API client for Verba FastAPI backend
   - [ ] Add authentication and API key management
   - [ ] Handle file uploads and downloads
   - [ ] Implement real-time progress updates via SSE

2. **Audio Recording**
   - [ ] Integrate AVFoundation for actual audio recording
   - [ ] Add audio file format conversion
   - [ ] Implement real microphone input waveform visualization
   - [ ] Add audio playback controls

3. **Data Persistence**
   - [ ] Implement CoreData or SwiftData models
   - [ ] Add local caching of recordings and transcripts
   - [ ] Implement offline mode support

4. **Settings & Configuration**
   - [ ] Build out Settings view
   - [ ] Add Whisper model selection
   - [ ] Add language preference
   - [ ] Add markdown style options
   - [ ] Store API keys securely in Keychain

5. **Testing**
   - [ ] Add unit tests for models and business logic
   - [ ] Add UI tests for critical user flows
   - [ ] Test on various iOS versions and devices

## License

Part of the Verba project. See repository root for license information.

## Original Application

This iOS app was originally named "Jiminy" and has been renamed to "Verba-M" to align with the Verba brand and ecosystem.
