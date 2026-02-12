# Verba-M Android App

Android mobile application for Verba - a media processing suite for transcribing video/audio files and summarizing transcripts using Whisper and LLMs.

## Overview

This Android app provides a mobile interface for the Verba platform, matching the iOS app's UX and design. Built with **Kotlin** and **Jetpack Compose**, it offers a modern, native Android experience.

### Key Features

- 🎙️ **Audio Recording**: Record meetings and conversations with live waveform visualization
- 📝 **Transcription**: Automatic speech-to-text conversion using OpenAI Whisper
- 🤖 **AI Summaries**: Generate structured summaries with key decisions, action items, and risks
- 📱 **Modern UI**: Material Design 3 with custom dark theme matching iOS design
- 🔄 **Real-time Progress**: Server-Sent Events (SSE) for live transcription updates
- 🏷️ **Classification Tags**: HIPAA, ADA, GINA, FCRA compliance tagging
- 🔒 **Sensitivity Levels**: Confidential, Highly Confidential, Restricted classifications

## Tech Stack

- **Language**: Kotlin
- **UI Framework**: Jetpack Compose (Material 3)
- **Navigation**: Compose Navigation
- **Networking**: Retrofit 2 + OkHttp 4
- **Architecture**: MVVM (ready for implementation)
- **Minimum SDK**: 26 (Android 8.0 Oreo)
- **Target SDK**: 34 (Android 14)

## Project Structure

```
android/
├── app/
│   ├── build.gradle.kts              # App-level build configuration
│   └── src/main/
│       ├── AndroidManifest.xml       # App permissions and configuration
│       ├── java/com/verba/verbam/
│       │   ├── MainActivity.kt       # App entry point with navigation
│       │   ├── api/
│       │   │   └── VerbaApiClient.kt # API client for backend communication
│       │   ├── models/
│       │   │   └── Recording.kt      # Data models and sample data
│       │   ├── navigation/
│       │   │   └── Screen.kt         # Navigation routes
│       │   ├── ui/
│       │   │   ├── screens/          # All screen composables
│       │   │   │   ├── SplashScreen.kt
│       │   │   │   ├── HomeScreen.kt
│       │   │   │   ├── RecordingScreen.kt
│       │   │   │   ├── TranscriptScreen.kt
│       │   │   │   ├── DetailScreen.kt
│       │   │   │   └── ProcessingScreen.kt
│       │   │   └── theme/
│       │   │       └── Theme.kt      # Color theme and design system
│       └── res/
│           ├── values/
│           │   ├── strings.xml       # App strings
│           │   └── themes.xml        # App theme
│           └── xml/
│               ├── backup_rules.xml
│               └── data_extraction_rules.xml
├── build.gradle.kts                  # Project-level build configuration
├── settings.gradle.kts               # Project settings
├── gradle.properties                 # Gradle properties
└── README.md                         # This file
```

## Screens

### 1. Splash Screen
- **Route**: `/splash`
- **Purpose**: Onboarding screen shown on first launch
- **Features**: 
  - Gradient background
  - Branded logo with mic icon
  - "Get Started" button
- **File**: `SplashScreen.kt`

### 2. Home Screen (Summaries List)
- **Route**: `/home`
- **Purpose**: View all recordings
- **Features**:
  - Search bar for filtering recordings
  - Recording cards with metadata (date, duration, word count)
  - "NEW" badge for recent recordings
  - Color-coded icons
- **File**: `HomeScreen.kt`

### 3. Recording Screen
- **Route**: `/record`
- **Purpose**: Record audio with live transcription
- **Features**:
  - Animated waveform (30 bars)
  - Real-time timer (MM:SS)
  - Pause/Stop/Bookmark controls
  - Live transcription preview
  - Blinking cursor animation
- **File**: `RecordingScreen.kt`

### 4. Transcript Screen
- **Route**: `/transcripts`
- **Purpose**: View transcript and AI summary
- **Features**:
  - Custom tab picker (Transcript / Summary)
  - Metadata badges (date, duration, word count)
  - Timestamped transcript entries
  - Structured summary cards with color coding:
    - Executive Summary (purple)
    - Key Decisions (green)
    - Technical Points (orange)
    - Risks (red)
    - Next Steps (blue)
- **File**: `TranscriptScreen.kt`

### 5. Detail Screen
- **Route**: `/detail/{recordingId}`
- **Purpose**: Manage recording metadata and tags
- **Features**:
  - Full metadata display
  - Classification tags (HIPAA, ADA, GINA, FCRA)
  - Sensitivity levels
  - Participants list
  - Summary preview
  - Bottom sheet for editing tags
- **File**: `DetailScreen.kt`

### 6. Processing Screen
- **Route**: `/processing/{jobId}`
- **Purpose**: Show AI processing progress
- **Features**:
  - Animated spinner (rotating gradient)
  - 5 processing steps with state indicators:
    - Done (green checkmark)
    - Active (purple with step number)
    - Pending (gray with step number)
  - Progress messages
- **File**: `ProcessingScreen.kt`

## Design System

### Color Palette

All colors match the iOS app's design:

```kotlin
// Dark backgrounds
themeBg = Color(0xFF0F0C29)          // rgb(15, 12, 41)
themeBgLight = Color(0xFF1A1A3E)     // rgb(26, 26, 62)

// Brand colors
themePurple = Color(0xFF667EEA)      // Primary
themeViolet = Color(0xFF764BA2)      // Secondary

// Status colors
themeGreen = Color(0xFF2ED573)       // Success
themeOrange = Color(0xFFFFA503)      // Warning
themeRed = Color(0xFFFF4757)         // Error
themeBlue = Color(0xFF1E90FF)        // Info

// Text opacity
cardBg = Color.White.copy(alpha = 0.04f)
subtleText = Color.White.copy(alpha = 0.45f)
bodyText = Color.White.copy(alpha = 0.65f)
primaryText = Color.White.copy(alpha = 0.85f)
```

### Typography

- **Page Titles**: 28-32sp, Bold
- **Section Headers**: 20-22sp, SemiBold
- **Body Text**: 13-15sp, Regular
- **Labels**: 11-12sp, SemiBold, uppercase with letter spacing
- **Timestamps**: 11sp, SemiBold, monospaced digits

## API Integration

### Backend Configuration

The app connects to the Verba backend at:

```
Base URL: https://localhost:30318/
```

### Endpoints

1. **Upload Audio**
   - `POST /api/audiotr/upload`
   - Multipart form data with audio file
   - Returns: `jobId` and `status`

2. **Get Job Status**
   - `GET /api/audiotr/jobs/{id}`
   - Returns: Job progress and result

3. **Job Progress (SSE)**
   - `GET /api/audiotr/jobs/{id}/progress`
   - Server-Sent Events stream
   - Real-time progress updates

4. **Generate Summary**
   - `POST /api/transtr/summarize`
   - Body: `{ transcriptText, instructions, model }`
   - Returns: AI-generated summary

### Usage Example

```kotlin
// Upload audio file
val file = File("/path/to/audio.m4a")
val response = VerbaApiClient.audioService.uploadAudio(
    file = file.toMultipartBody(),
    model = "base".toRequestBody(),
    language = "en".toRequestBody()
)

// Listen to progress via SSE
val eventSource = VerbaApiClient.createEventSource(
    url = "api/audiotr/jobs/${jobId}/progress",
    listener = object : EventSourceListener() {
        override fun onEvent(
            eventSource: EventSource,
            id: String?,
            type: String?,
            data: String
        ) {
            // Parse progress data
            val progress = parseProgress(data)
            updateUI(progress)
        }
    }
)
```

## Getting Started

### Prerequisites

- **Android Studio**: Hedgehog (2023.1.1) or later
- **JDK**: 17 or later
- **Android SDK**: API 34
- **Verba Backend**: Running at `https://localhost:30318`

### Setup Steps

1. **Open Project in Android Studio**
   ```bash
   cd android/
   # Open in Android Studio
   ```

2. **Sync Gradle**
   - Android Studio will automatically prompt to sync
   - Or: File → Sync Project with Gradle Files

3. **Configure Backend URL**
   - Edit `app/src/main/java/com/verba/verbam/api/VerbaApiClient.kt`
   - Update `BASE_URL` if your backend is on a different host/port
   - For emulator: Use `10.0.2.2` instead of `localhost`
   - For physical device: Use your computer's IP address

4. **Grant Permissions**
   - The app requests `RECORD_AUDIO` permission at runtime
   - Ensure microphone access is granted in device settings

5. **Run App**
   - Select device/emulator
   - Click Run ▶️ or press Shift+F10

### Build Variants

- **Debug**: Development build with logging
- **Release**: Production build (requires signing configuration)

## Current Status

### ✅ Implemented

- [x] Complete UI matching iOS design
- [x] Navigation with bottom tabs
- [x] All 6 screens with full UX
- [x] Animated waveform visualizer
- [x] Processing progress with step indicators
- [x] Custom color theme
- [x] API client with Retrofit
- [x] SSE support for real-time updates
- [x] Sample data for testing

### 🚧 TODO (Future Enhancements)

- [ ] **Audio Recording**: Implement `MediaRecorder` for actual recording
- [ ] **File Storage**: Save recordings to local storage
- [ ] **Data Persistence**: Room database for offline support
- [ ] **ViewModel Layer**: MVVM architecture with state management
- [ ] **Permission Handling**: Runtime permission requests
- [ ] **Error Handling**: User-friendly error messages
- [ ] **Loading States**: Skeleton screens and shimmer effects
- [ ] **Pull-to-Refresh**: Refresh recordings list
- [ ] **Search Functionality**: Full-text search within transcripts
- [ ] **Export Features**: Share/download transcripts and summaries
- [ ] **Settings Screen**: User preferences and API key management
- [ ] **Background Work**: WorkManager for uploads/processing
- [ ] **Notifications**: Show progress notifications
- [ ] **SSL Certificate**: Proper certificate validation for HTTPS
- [ ] **Testing**: Unit tests and UI tests

## Development Notes

### iOS vs Android Mapping

| iOS (SwiftUI) | Android (Compose) |
|---------------|-------------------|
| `@State` | `mutableStateOf()` with `remember` |
| `@Binding` | State + lambda callbacks |
| `NavigationStack` | `NavHost` + `NavController` |
| `TabView` | `Scaffold` + `NavigationBar` |
| `Sheet` | `ModalBottomSheet` |
| `List` | `LazyColumn` |
| `HStack` | `Row` |
| `VStack` | `Column` |
| `ZStack` | `Box` |

### Known Issues

1. **SSL Certificate**: Currently bypasses SSL validation for localhost development
   - **Fix**: Implement proper certificate pinning for production
   
2. **Sample Data Only**: App uses hardcoded sample data
   - **Fix**: Integrate with backend API endpoints

3. **No Real Recording**: Recording screen is UI-only
   - **Fix**: Implement `MediaRecorder` API

4. **Onboarding State**: Resets on app restart
   - **Fix**: Save to DataStore for persistence

## Contributing

When adding new features:

1. Follow existing code style and patterns
2. Use type annotations for all functions
3. Add docstrings for public functions
4. Match iOS UX behavior when possible
5. Test on multiple screen sizes
6. Ensure dark theme compatibility

## License

This project is part of the Verba platform. See the main repository for license information.

## Support

For issues or questions:
- Check the main Verba repository
- Review the web app documentation in `web/`
- Compare with iOS implementation in `ios/`

---

**Built with Kotlin and Jetpack Compose** • **Matching iOS UX** • **Ready for Backend Integration**
