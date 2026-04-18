"""Server-side token usage accumulator.

Stores cumulative token usage per user in a JSON file so usage summaries
can be shown across all clients and all time (not just per-session).
"""

import json
import os
import threading

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
USAGE_PATH = os.path.join(BASE_DIR, ".klodTalk", "usage", "token_usage.json")


class TokenStore:
    def __init__(self):
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if os.path.isfile(USAGE_PATH):
            try:
                with open(USAGE_PATH) as f:
                    data = json.load(f)
                if isinstance(data, dict) and "users" in data:
                    return data
            except Exception:
                pass
        return {"users": {}}

    def _write(self, data: dict):
        os.makedirs(os.path.dirname(USAGE_PATH), exist_ok=True)
        with open(USAGE_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def add_tokens(self, user_name: str, input_tokens: int, output_tokens: int, cost_usd: float):
        with self._lock:
            data = self._read()
            user = data["users"].setdefault(user_name, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
            user["input_tokens"] += input_tokens
            user["output_tokens"] += output_tokens
            user["cost_usd"] += cost_usd
            self._write(data)

    def add_step_tokens(self, user_name: str, session_id: str, step_name: str,
                        input_tokens: int, output_tokens: int, cost_usd: float):
        """Record token usage for a specific pipeline step within a session."""
        with self._lock:
            data = self._read()
            user = data["users"].setdefault(user_name, {
                "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0
            })
            sessions = user.setdefault("sessions", {})
            session = sessions.setdefault(session_id, {
                "steps": {}, "total_input": 0, "total_output": 0, "total_cost": 0.0
            })
            step = session["steps"].setdefault(step_name, {
                "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0
            })
            step["input_tokens"] += input_tokens
            step["output_tokens"] += output_tokens
            step["cost_usd"] += cost_usd
            session["total_input"] += input_tokens
            session["total_output"] += output_tokens
            session["total_cost"] += cost_usd
            self._write(data)

    def get_session_breakdown(self, user_name: str, session_id: str) -> dict:
        """Get per-step token breakdown for a specific session."""
        with self._lock:
            data = self._read()
        user = data.get("users", {}).get(user_name, {})
        sessions = user.get("sessions", {})
        return sessions.get(session_id, {
            "steps": {}, "total_input": 0, "total_output": 0, "total_cost": 0.0
        })

    def get_summary(self) -> dict:
        with self._lock:
            data = self._read()
        users = data.get("users", {})
        total_in = sum(u.get("input_tokens", 0) for u in users.values())
        total_out = sum(u.get("output_tokens", 0) for u in users.values())
        total_cost = sum(u.get("cost_usd", 0.0) for u in users.values())
        return {
            "per_user": {k: dict(v) for k, v in users.items()},
            "all_users": {
                "input_tokens": total_in,
                "output_tokens": total_out,
                "cost_usd": total_cost,
            },
        }
