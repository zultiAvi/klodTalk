# Development Guide

## Running Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

Tests are designed to work without Docker, Claude CLI, or real credentials. The `conftest.py` provides fixtures that mock external dependencies.

## Adding a New OS Backend

1. Create `server/utils/os/windows.py` (or `darwin.py`)
2. Implement `OsUtilsBase` from `server/utils/os/base.py`
3. Register it in `server/utils/os/__init__.py`

## Adding a New Git Protocol

1. Create `server/utils/git/<protocol>.py`
2. Implement `GitUtilsBase` from `server/utils/git/base.py`
3. Register it in `server/utils/git/__init__.py`
4. Add the protocol option to `config/server_config.yaml`

## Adding a New Claude Auth Method

1. Create `server/utils/claude_auth/<method>.py`
2. Implement `ClaudeAuthBase` from `server/utils/claude_auth/base.py`
3. Register it in `server/utils/claude_auth/__init__.py`
4. Add the method option to `config/server_config.yaml`

## Project Structure

- `server/` — Python server + Docker agent runtime
- `clients/` — Android, web, and iOS clients
- `teams/` — Team pipeline configs, member roles, orchestration scripts
- `config/` — Static configuration
- `helpers/` — CLI management tools
- `tests/` — Unit tests
- `docs/` — Documentation
