---
name: dataclass-over-dict-getattr
summary: "Prefer @dataclass with default fields over dicts plus getattr(obj, 'field', default) — declare the field on the class so missing-field bugs fail fast."
---

# Dataclass Over Dict + `getattr` Default

## Anti-pattern

```python
def handle(msg):
    session_id = msg.get("session_id", "")
    content    = msg.get("content", "")
    timeout    = getattr(msg, "timeout", 30.0)
    return run(session_id, content, timeout)
```

Problems:
- Typos in keys silently return the default.
- The contract of `msg` is invisible at the call site.
- IDE and type-checker get nothing.

## Preferred pattern

```python
from dataclasses import dataclass

@dataclass
class IncomingMessage:
    session_id: str
    content: str
    timeout: float = 30.0

def handle(msg: IncomingMessage):
    return run(msg.session_id, msg.content, msg.timeout)
```

A missing `session_id` raises at construction, an unknown attribute is a type error, and the default for `timeout` lives in one place.

## When dicts are still right

Use a plain `dict[str, T]` when the keys are data, not schema — e.g., `sessions_by_id: dict[str, Session]`.
