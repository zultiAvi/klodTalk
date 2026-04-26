#!/usr/bin/env python3
"""Rate limit awareness utilities for KlodTalk agent spawning.

Uses the Anthropic Rate Limits API (available April 2026) to proactively
check remaining request/token headroom before spawning agent batches.

NOTE: This utility only works with API key authentication. OAuth sessions
(browser-auth) do not have an API key; callers must handle the None return.

Reference: https://docs.anthropic.com/en/release-notes/api (April 2026)
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Optional

RATE_LIMITS_URL = "https://api.anthropic.com/v1/rate_limits"
_DEFAULT_TIMEOUT_S = 5


def query_rate_limit_headroom(api_key: Optional[str]) -> Optional[dict]:
    """Query the Anthropic Rate Limits API and return remaining headroom.

    Args:
        api_key: Anthropic API key (sk-ant-...). If None or empty, returns None.

    Returns:
        A dict with keys:
          - requests_remaining (int): requests left in the current window
          - tokens_remaining (int): input tokens left in the current window
          - reset_at (str): ISO-8601 UTC timestamp when limits reset
          - raw (dict): the full API response
        Returns None if the API key is absent, or if the request fails.
    """
    if not api_key:
        return None

    req = urllib.request.Request(
        RATE_LIMITS_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None

    # The API returns a list of limit objects; aggregate by finding the most
    # restrictive (smallest remaining) across all rate limit tiers.
    limits = data if isinstance(data, list) else data.get("rate_limits", [])
    if not limits:
        return {"requests_remaining": None, "tokens_remaining": None, "reset_at": None, "raw": data}

    min_requests = None
    min_tokens = None
    soonest_reset = None

    for limit in limits:
        req_rem = limit.get("requests_remaining")
        tok_rem = limit.get("tokens_remaining")
        reset = limit.get("reset_at") or limit.get("reset")

        if req_rem is not None:
            if min_requests is None or req_rem < min_requests:
                min_requests = req_rem
        if tok_rem is not None:
            if min_tokens is None or tok_rem < min_tokens:
                min_tokens = tok_rem
        if reset:
            if soonest_reset is None or reset < soonest_reset:
                soonest_reset = reset

    return {
        "requests_remaining": min_requests,
        "tokens_remaining": min_tokens,
        "reset_at": soonest_reset,
        "raw": data,
    }


def should_throttle(
    headroom: Optional[dict],
    min_requests: int = 5,
    min_tokens: int = 10_000,
) -> bool:
    """Return True if the agent spawner should pause before starting another agent.

    Args:
        headroom: result of query_rate_limit_headroom(), or None.
        min_requests: minimum request headroom to proceed without throttling.
        min_tokens: minimum token headroom to proceed without throttling.

    Returns:
        True if throttling is recommended; False otherwise.
    """
    if headroom is None:
        return False  # No API key -- can't know; don't block.

    req_rem = headroom.get("requests_remaining")
    tok_rem = headroom.get("tokens_remaining")

    if req_rem is not None and req_rem < min_requests:
        return True
    if tok_rem is not None and tok_rem < min_tokens:
        return True
    return False


def wait_for_reset(headroom: Optional[dict], max_wait_s: int = 60) -> None:
    """Sleep until the rate limit resets, up to max_wait_s seconds.

    Typically called after should_throttle() returns True. Uses exponential
    back-off if the reset_at timestamp is unavailable.

    Args:
        headroom: result of query_rate_limit_headroom(), or None.
        max_wait_s: maximum seconds to sleep regardless of reset_at.
    """
    if headroom is None:
        return

    reset_at = headroom.get("reset_at")
    if reset_at:
        try:
            reset_dt = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            wait_s = (reset_dt - now).total_seconds()
            if 0 < wait_s < max_wait_s:
                time.sleep(wait_s)
                return
        except (ValueError, TypeError):
            pass

    # Fallback: exponential back-off starting at 5 s
    time.sleep(min(5, max_wait_s))
