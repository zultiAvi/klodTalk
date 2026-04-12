# KlodTalk iOS Client

This is a placeholder for a future iOS client.

## Current Status

We don't have access to a Mac for iOS development. The KlodTalk system works with the **Android app** and **web client** — both connect via the same WebSocket protocol.

## Contributing an iOS App

If you have a Mac and want to build an iOS client, you're welcome to contribute! The app needs to:

1. **Connect via WebSocket** to the KlodTalk server (wss://server:port)
2. **Authenticate** with a `hello` message containing `name` and `password_hash` (SHA-256)
3. **Send voice input** as text messages (type: `text`, with `project` and `content` fields)
4. **Receive responses** (type: `response`, with `project` and `content` fields)
5. **Display project list** from the `projects` message (type: `projects`)

See `clients/web/index.html` for a complete reference implementation of the protocol.

The Android app at `clients/android/` shows how to implement speech-to-text, project selection, and session management.

## Protocol Reference

| Direction | Type | Fields |
|-----------|------|--------|
| Client -> Server | `hello` | `name`, `password_hash` |
| Server -> Client | `projects` | `projects` (list of `{name, description}`) |
| Client -> Server | `text` | `project`, `content` |
| Server -> Client | `response` | `project`, `content` |

All messages are JSON over WebSocket.
