#!/usr/bin/env python3
"""Per-user unread session tracking."""

import json
import logging
import os

log = logging.getLogger("klodtalk.unread")

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
UNREAD_STATE_PATH = os.path.join(BASE_DIR, ".klodTalk", "state", "unread_state.json")


class UnreadState:
    def __init__(self):
        self._state: dict[str, list[str]] = {}
        self.load()

    def load(self):
        if not os.path.isfile(UNREAD_STATE_PATH):
            self._state = {}
            return
        try:
            with open(UNREAD_STATE_PATH) as f:
                self._state = json.load(f)
        except Exception as e:
            log.error("Failed to load unread state: %s", e)
            self._state = {}

    def save(self):
        try:
            os.makedirs(os.path.dirname(UNREAD_STATE_PATH), exist_ok=True)
            with open(UNREAD_STATE_PATH, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            log.error("Failed to save unread state: %s", e)

    def mark_unread(self, session_id: str, users: list[str]):
        for user in users:
            if user not in self._state:
                self._state[user] = []
            if session_id not in self._state[user]:
                self._state[user].append(session_id)
        self.save()

    def mark_read(self, session_id: str, user_name: str):
        if user_name in self._state:
            self._state[user_name] = [
                s for s in self._state[user_name] if s != session_id
            ]
            self.save()

    def get_unread(self, user_name: str) -> list[str]:
        return list(self._state.get(user_name, []))
