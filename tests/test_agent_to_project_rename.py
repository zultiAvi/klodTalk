"""Tests for the agent→project rename across the codebase.

These tests verify that the KlodTalk session/workspace concept has been
renamed from "agent" to "project" everywhere it should be, while keeping
"agent" where it refers to the Claude AI agent runtime.
"""

import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def _read(relpath: str) -> str:
    with open(os.path.join(ROOT, relpath)) as f:
        return f.read()


# ── Phase 1: Config & Data Structure Tests ──────────────────────────────────

class TestConfigRenames:
    def test_projects_json_exists(self):
        assert os.path.isfile(os.path.join(ROOT, "config", "projects.json.example"))

    def test_no_agents_json_example(self):
        assert not os.path.isfile(os.path.join(ROOT, "config", "agents.json.example"))

    def test_gitignore_references_projects_json(self):
        content = _read(".gitignore")
        assert "config/projects.json" in content
        assert "config/agents.json" not in content

    def test_add_project_script_exists(self):
        assert os.path.isfile(os.path.join(ROOT, "helpers", "add_project.py"))

    def test_no_add_agent_script(self):
        assert not os.path.isfile(os.path.join(ROOT, "helpers", "add_agent.py"))


# ── Phase 2: Server Code Structure Tests ────────────────────────────────────

class TestServerCodeStructure:
    def test_server_has_projects_path(self):
        content = _read("server/server.py")
        assert "PROJECTS_PATH" in content
        assert "AGENTS_PATH" not in content

    def test_server_load_projects_function(self):
        content = _read("server/server.py")
        assert "def load_projects()" in content
        assert "def load_agents()" not in content

    def test_server_get_projects_for_user(self):
        content = _read("server/server.py")
        assert "def get_projects_for_user(" in content
        assert "def get_agents_for_user(" not in content

    def test_server_get_project_record(self):
        content = _read("server/server.py")
        assert "def get_project_record(" in content
        assert "def get_agent_record(" not in content

    def test_session_has_project_name(self):
        content = _read("server/session_manager.py")
        assert "project_name: str" in content
        assert "agent_name: str" not in content

    def test_session_has_project_folder(self):
        content = _read("server/session_manager.py")
        assert "project_folder: str" in content
        assert "agent_folder: str" not in content

    def test_sanitize_image_uses_project(self):
        content = _read("server/session_manager.py")
        assert "def sanitize_image_name(project_name" in content
        assert "def sanitize_image_name(agent_name" not in content

    def test_project_name_env_var_in_session_manager(self):
        content = _read("server/session_manager.py")
        assert "PROJECT_NAME=" in content
        assert "AGENT_NAME=" not in content


# ── Phase 3: WebSocket Protocol Tests ───────────────────────────────────────

class TestWebSocketProtocol:
    def test_protocol_uses_projects_message_type(self):
        content = _read("server/server.py")
        assert '"type": "projects"' in content
        assert '"type": "agents"' not in content

    def test_protocol_uses_project_field(self):
        content = _read("server/server.py")
        # The "project" field should appear in outgoing messages
        assert '"project": session.project_name' in content or '"project":' in content
        # "agent" field should NOT appear (except "role": "agent" which is kept)
        # Check new_message broadcasts don't use "agent" key for the project name
        assert '"agent": session.project_name' not in content
        assert '"agent": session.agent_name' not in content

    def test_new_session_uses_project_field(self):
        content = _read("server/server.py")
        # handle_new_session should use project_name and "project" field
        assert 'data.get("project"' in content
        assert 'data.get("agent"' not in content


# ── Phase 4: Client-Side Tests ──────────────────────────────────────────────

class TestWebClient:
    def test_web_client_no_agent_picker(self):
        content = _read("clients/web/index.html")
        assert "agent-picker" not in content

    def test_web_client_has_project_picker(self):
        content = _read("clients/web/index.html")
        assert "project-picker" in content

    def test_web_client_choose_project_title(self):
        content = _read("clients/web/index.html")
        assert "Choose a Project" in content
        assert "Choose an Agent" not in content


# ── Phase 5: Documentation Tests ────────────────────────────────────────────

class TestDocumentation:
    def test_readme_no_agents_json_reference(self):
        content = _read("README.md")
        assert "agents.json" not in content

    def test_readme_no_add_agent_reference(self):
        content = _read("README.md")
        assert "add_agent.py" not in content

    def test_config_claude_md_uses_projects(self):
        content = _read("config/CLAUDE.md")
        assert "projects.json" in content
        assert "agents.json" not in content

    def test_helpers_claude_md_uses_projects(self):
        content = _read("helpers/CLAUDE.md")
        assert "add_project.py" in content
        assert "add_agent.py" not in content


# ── Phase 6: Run Agent Env Var Tests ────────────────────────────────────────

class TestRunAgentEnvVars:
    def test_run_agent_py_uses_project_name_env(self):
        content = _read("server/run_agent.py")
        assert "PROJECT_NAME" in content
        assert "AGENT_NAME" not in content

    def test_run_agent_sh_uses_project_name_env(self):
        content = _read("server/run_agent.sh")
        assert "PROJECT_NAME" in content
        assert "AGENT_NAME" not in content
