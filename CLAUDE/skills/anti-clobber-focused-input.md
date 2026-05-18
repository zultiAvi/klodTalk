---
skill_name: anti-clobber-focused-input
triggers:
  - Adding a collaborative/multi-user editable text field
  - Wiring a server-pushed value into a client text input
  - Diagnosing "my edit disappeared while typing"
summary: When a WebSocket update arrives for a field the user is currently editing, skip the local refresh so the in-progress edit isn't clobbered. Apply on both web and Android.
---

# Skill: Anti-Clobber Pattern for Collaborative Text Fields

## Quick Reference
- Web: gate the refresh on `document.activeElement !== inputEl`.
- Android Compose: gate `LaunchedEffect` on a `focused` boolean that you flip in `Modifier.onFocusChanged`.
- Always save the user's edit on `blur` / focus loss / IME Done — not on every keystroke.
- No-op the save when the trimmed draft equals the server's current value.

## When to Use
Any time a text input is bound to a server-pushed value that other users can also change: session comments, project names, shared notes, collaborative titles.

## Web Pattern (vanilla JS)

```javascript
// On WebSocket update for the field
case 'session_comment_updated':
  if (sessions[msg.session_id]) {
    sessions[msg.session_id].comment = msg.comment || '';
    if (currentSessionId === msg.session_id) {
      const el = document.getElementById('history-comment-input');
      // Skip refresh if the user is currently typing in this field.
      if (el && document.activeElement !== el) el.value = msg.comment || '';
    }
    renderSessionsList();
  }
  break;

// Save helper — only sends if changed and socket open.
function saveSessionComment() {
  const val = inputEl.value.trim();
  const cur = (sessions[currentSessionId] || {}).comment || '';
  if (val === cur) return;
  ws.send(JSON.stringify({ type: 'set_session_comment', session_id: currentSessionId, comment: val }));
}
```

Wire `onblur="saveSessionComment()"` and `onkeydown="if(event.key==='Enter'){event.preventDefault();this.blur();}"` on the input.

## Android Compose Pattern

```kotlin
var commentDraft by remember(currentSessionId) { mutableStateOf(session?.comment ?: "") }
var commentFocused by remember { mutableStateOf(false) }

LaunchedEffect(session?.comment, currentSessionId) {
    // Only refresh from server when the user is NOT actively editing.
    if (!commentFocused) commentDraft = session?.comment ?: ""
}

OutlinedTextField(
    value = commentDraft,
    onValueChange = { commentDraft = it.take(500) },
    modifier = Modifier.onFocusChanged { state ->
        val wasFocused = commentFocused
        commentFocused = state.isFocused
        if (wasFocused && !state.isFocused) {
            // Focus lost → save if changed.
            val server = session?.comment ?: ""
            if (commentDraft.trim() != server) {
                viewModel.setSessionComment(currentSessionId, commentDraft.trim())
            }
        }
    },
    keyboardActions = KeyboardActions(onDone = { focusManager.clearFocus() }),
    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
)
```

## Why
Without this guard, every broadcast (including the user's OWN echo from the server) will overwrite the text input while they're mid-keystroke, dropping characters and moving the caret. The pattern preserves the "last writer wins" semantics but only at focus-loss boundaries, which is the intuitive UX.
