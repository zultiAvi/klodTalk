# clients/android/

The Android client. Currently the only native mobile app (iOS is a future phase).

## Why a Native Android App

Voice is the primary input method. Android's `SpeechRecognizer` gives high-quality, low-latency speech-to-text with streaming partial results — better than what the Web Speech API offers in most browsers. A native app also means:

- Background operation and foreground service notifications.
- System-level audio and microphone control.
- Reliable TTS through Android's `TextToSpeech` engine.
- Works without a browser tab staying open.

## Architecture Decisions

**Single-Activity, Jetpack Compose.** The app uses a single Activity switching between composables — simpler than fragments or multi-activity navigation. The ViewModel holds all state.

**ViewModel owns everything.** `MainViewModel` manages WebSocket connection, speech recognition, TTS, app state, and settings. This keeps the composable screens stateless and purely declarative. The ViewModel survives configuration changes (rotation), so the WebSocket connection stays alive.

**State machine for the main flow.** The `AppState` enum (IDLE → LISTENING → PROCESSING → REVIEW → ADDING → ADD_PROCESSING) makes the UI deterministic. Each state maps to a distinct visual layout. No ambiguous "half-listening, half-reviewing" states.

**OkHttp for WebSocket.** Android's standard HTTP library, reliable for persistent WebSocket connections. The client authenticates immediately on connect by sending a `hello` message with the SHA-256 password hash.

**Settings stored in SharedPreferences.** Server IP, port, username, and password persist across app restarts. On first launch, the Settings screen is shown. After connecting once, the app goes straight to the Main screen.

## Screen Flow

1. **Settings** — Configure server connection. Shown on first launch or when tapping the settings icon.
2. **Sessions** — Session list per project: create, rename, delete, switch sessions. Swipe-to-delete with undo.
3. **Main** — Project selector dropdown, "Start Talking" button (speech), "Type Instead" (manual input). After speaking, the text goes to Review.
4. **Review** — Edit the transcribed text. Hear it back (TTS), Add more speech, Paste clipboard, Send to project, or Cancel.
5. **History** — View full message history for a session with styled messages.
6. **Inbox** — Project responses arrive here. Per-project tabs, each message can be read aloud (TTS) or answered.

## Key Files

- `MainActivity.kt` — Entry point, permissions, screen navigation.
- `viewmodel/MainViewModel.kt` — All app state and business logic.
- `network/WebSocketClient.kt` — WebSocket connection, auth, message send/receive.
- `network/SendMode.kt` — Confirm/Execute mode enum for message sending.
- `ui/screens/SettingsScreen.kt` — Connection settings form.
- `ui/screens/SessionsScreen.kt` — Session management (create, rename, delete, switch).
- `ui/screens/MainScreen.kt` — Main voice interaction UI.
- `ui/screens/HistoryScreen.kt` — Session message history viewer.
- `ui/screens/IncomingMessagesScreen.kt` — Inbox for project responses.
- `ui/screens/MessageStyleMapper.kt` — Markdown-to-styled-text rendering.
- `ui/theme/Theme.kt` — Material 3 theming with dynamic colors on Android 12+.
