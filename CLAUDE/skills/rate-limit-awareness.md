# Skill: Rate Limit Awareness

## When to Use
When the server is spawning multiple concurrent agent sessions, when diagnosing 429 errors from the Anthropic API, or when adding proactive throttling before agent batch launches.

## Background

Anthropic's Rate Limits API (released April 2026) allows programmatic querying of remaining request and token headroom for the current API key + workspace. This enables proactive throttling before hard 429 errors occur, rather than absorbing failures and retrying reactively.

KlodTalk spawns one Docker agent per active project session. Under multi-user load, parallel agents can exhaust rate limits simultaneously.

**Important**: The Rate Limits API requires an API key (`x-api-key` header). OAuth sessions (browser-authenticated agents) do not have an API key -- all functions in `rate_limit_utils.py` return `None` in that case and callers fall back to reactive 429 handling. Never block agent spawning solely because `query_rate_limit_headroom()` returned `None`.

## Utility Location

`server/utils/rate_limit_utils.py`

### Key Functions

```python
from utils.rate_limit_utils import query_rate_limit_headroom, should_throttle, wait_for_reset

# Check headroom before spawning an agent
api_key = os.environ.get("ANTHROPIC_API_KEY")
headroom = query_rate_limit_headroom(api_key)

if should_throttle(headroom):
    wait_for_reset(headroom, max_wait_s=60)

# Now spawn the agent
```

### `query_rate_limit_headroom(api_key) -> dict | None`
Returns:
- `requests_remaining` (int): requests left in the current window
- `tokens_remaining` (int): input tokens left in the current window
- `reset_at` (str): ISO-8601 UTC timestamp when limits reset
- `raw` (dict): full API response

Returns `None` if api_key is absent or the API call fails.

### `should_throttle(headroom, min_requests=5, min_tokens=10_000) -> bool`
Returns `True` if throttling is recommended based on remaining headroom.

### `wait_for_reset(headroom, max_wait_s=60)`
Sleeps until the rate limit resets (up to `max_wait_s` seconds). Uses the `reset_at` timestamp if available; falls back to a 5-second exponential back-off.

## Integration Point

The recommended integration point is `server/session_manager.py` in the `_launch_agent()` method (or equivalent), immediately before the `docker exec` call that spawns a new agent. This is a restricted file -- do not modify it without explicit instruction.

## Recommended Throttle Thresholds

| Environment | min_requests | min_tokens |
|-------------|-------------|-----------|
| Development (1-2 users) | 2 | 5,000 |
| Production (multi-user) | 5 | 10,000 |
| CI/nightly pipeline | 3 | 5,000 |

## Fallback Behavior

If `query_rate_limit_headroom()` returns `None` (OAuth auth, network error, or API unavailable), `should_throttle()` returns `False` and the agent spawner proceeds normally. The existing 429 retry logic in the server handles the failure case.
