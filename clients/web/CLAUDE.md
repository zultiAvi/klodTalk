# clients/web/

A browser-based client that mirrors the Android app's functionality. A single HTML file, no build step, no dependencies.

## Why a Web Client

The Android app requires an APK build, a phone, and installation. The web client gives instant access from any device with a browser — useful when your phone isn't nearby, when testing, or when someone else needs quick access without installing anything. It implements the exact same WebSocket protocol as the Android app, so the server can't tell the difference.

## Why a Single HTML File

- **Zero build tooling.** Open the file in a browser and it works. No npm, no bundler, no dev server needed.
- **Easy to deploy.** Copy one file. Serve it with `python -m http.server` or just open it as `file://`.
- **Self-contained.** All CSS and JS are inline. No external CDN dependencies that could break.
- **Good enough for the use case.** The UI has four views (Settings, Main, Review, Inbox) with straightforward state transitions. This doesn't need React.

## Design Decisions

**Web Speech API for voice input.** `webkitSpeechRecognition` provides the same speech-to-text flow as Android: continuous listening, interim results shown live, final text goes to review. Works best in Chrome/Edge; limited in Firefox.

**SpeechSynthesis for TTS.** Read responses aloud, hear your own text before sending. Uses the browser's built-in voices.

**SHA-256 hashing via SubtleCrypto.** Password is hashed client-side before sending, same as the Android app. Uses the native Web Crypto API — no libraries needed.

**localStorage for settings.** Server IP, port, username, and password persist across browser sessions, same pattern as SharedPreferences on Android.

**Dark mode via `prefers-color-scheme`.** Respects the system preference automatically. No manual toggle — keeps the UI simple.

## Key Invariants

**`reviewDraft` sequencing** — `reviewDraft` must only be cleared in `goToReview()` (or explicitly by `setReviewDraft('')`), never in `stopListening()`. The reason: `stopListening()` calls `goToReview()` immediately, but the user may cancel that recording session. Clearing `reviewDraft` in `stopListening()` would silently discard a saved draft before the user has had a chance to see the new text. `goToReview()` is the authoritative place that decides when old draft state is superseded.

**`showPage` draft opt-in** — `showPage(name, { saveDraft: true })` saves the textarea content to `reviewDraft` when navigating away from review. The default (`saveDraft = false`) does NOT save. This opt-in design means callers that don't care about drafts (sending, cancelling) can't accidentally resurrect sent text. Only navigation actions that the user might want to undo (header Messages, header Settings, title link) pass `saveDraft: true`.

**`draftLoadedInTextarea` flag** — tracks whether the textarea DOM element currently holds the saved `reviewDraft` value (relying on the browser preserving hidden-element values). Set to `true` in `showPage` when a draft is saved; cleared by `setReviewDraft('')`. `setReviewDraft` deliberately does NOT set this flag for non-empty values — the caller in `showPage` sets it after writing the value to the DOM, because only that code knows the textarea has been updated. Used in `goToReview()` to suppress the redundant "Resume editing" button when the draft is already loaded, without relying on fragile textarea-content comparisons.

## Limitations

- Web Speech API requires Chrome or Edge for reliable operation.
- No background notifications when the tab isn't active.
- WebSocket uses `wss://` (TLS-encrypted) with a self-signed certificate. The user must trust the cert in the browser first by visiting `https://<server-ip>:3174`.
- The server does not serve this file. You open it separately or host it with any static file server.
