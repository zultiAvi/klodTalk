# clients/

Client applications that connect to the KlodTalk server via WebSocket.

## android/

Android client built with Kotlin and Jetpack Compose. Provides speech-to-text input, project selection, message history, and a review inbox. See `clients/android/CLAUDE.md` for details.

## web/

Browser-based client in a single HTML file (`index.html`). Uses the Web Speech API for voice input and SubtleCrypto for password hashing. Zero external dependencies.

## ios/

Placeholder for a future iOS client. See `clients/ios/README.md`.

All clients speak the same WebSocket JSON protocol and are interchangeable.
