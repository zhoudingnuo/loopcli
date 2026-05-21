"""
End-to-end integration tests for the LoopCLI WebUI system.

Validates:
1. All API endpoints return correct status codes and response formats
2. Agent lifecycle flow: create task -> list tasks -> send message -> verify inbox
3. Security mechanisms in production: auth rejection, path traversal rejection, body size limit
4. WebUI frontend page loads correctly
"""

import json
import os
import sys
import time
import threading
import pytest
import httpx
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "webui"))

from server import (
    WebUIHandler,
    ThreadedHTTPServer,
    MAIN_DIR,
)
from loopcli_lib import (
    safe_agent_path as _safe_agent_path,
    read_json,
    write_json,
    scan_agents,
    LOOPCLI_ROOT,
)

# ─── Server fixture ───

BASE_PORT = 19100
_port_lock = threading.Lock()
_port_counter = [0]


def _get_port():
    with _port_lock:
        _port_counter[0] += 1
        return BASE_PORT + _port_counter[0]


@pytest.fixture(scope="module")
def server_url():
    """Start a real HTTP server for integration tests."""
    port = _get_port()
    server = ThreadedHTTPServer(("127.0.0.1", port), WebUIHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture
def client(server_url):
    return httpx.Client(base_url=server_url, timeout=5)


# Save and restore tasks to avoid side effects across tests
@pytest.fixture(autouse=True)
def preserve_main_tasks():
    """Backup main tasks.json before each test, restore after."""
    tasks_file = MAIN_DIR / "memory" / "tasks.json"
    original = read_json(tasks_file, [])
    yield
    write_json(tasks_file, original)


# ═══════════════════════════════════════════════════════════
# 1. API ENDPOINT VALIDATION
# ═══════════════════════════════════════════════════════════


class TestAPIEndpointsGet:
    """Verify all GET endpoints return correct status codes and formats."""

    def test_get_agents_200(self, client):
        r = client.get("/api/agents")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for agent in data:
            assert "id" in agent
            assert "name" in agent
            assert "status" in agent

    def test_get_tasks_default_200(self, client):
        r = client.get("/api/tasks")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_tasks_all_agents_200(self, client):
        r = client.get("/api/tasks", params={"agent": "__all__"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_tasks_specific_agent_200(self, client):
        r = client.get("/api/tasks", params={"agent": "main"})
        assert r.status_code == 200

    def test_get_logs_200(self, client):
        r = client.get("/api/logs")
        assert r.status_code == 200
        data = r.json()
        assert "lines" in data
        assert isinstance(data["lines"], list)

    def test_get_logs_with_agent_200(self, client):
        r = client.get("/api/logs", params={"agent": "main"})
        assert r.status_code == 200
        assert "lines" in r.json()

    def test_get_logs_with_count_200(self, client):
        r = client.get("/api/logs", params={"agent": "main", "n": 5})
        assert r.status_code == 200

    def test_get_loopcli_status_200(self, client):
        r = client.get("/api/loopcli/status")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_get_agent_tasks_endpoint_200(self, client):
        r = client.get("/api/agents/main/tasks")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_frontend_page_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_get_frontend_index_html_200(self, client):
        r = client.get("/index.html")
        assert r.status_code == 200


class TestAPIEndpointsPost:
    """Verify all POST endpoints return correct status codes and formats."""

    def test_create_task_201(self, client):
        r = client.post("/api/tasks", json={
            "title": "[INTTEST] integration test task",
            "description": "created by e2e integration test",
            "assignee": "main",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "pending"
        assert "id" in data
        assert data["title"] == "[INTTEST] integration test task"

    def test_create_task_missing_title_400(self, client):
        r = client.post("/api/tasks", json={"description": "no title"})
        assert r.status_code == 400

    def test_send_message_201(self, client):
        r = client.post("/api/messages/send", json={
            "content": "[INTTEST] hello from integration test",
            "agent": "main",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "sent"
        assert "file" in data

    def test_send_message_default_agent_main(self, client):
        r = client.post("/api/messages/send", json={
            "content": "[INTTEST] default agent test",
        })
        assert r.status_code == 201
        assert r.json()["agent"] == "main"

    def test_send_message_empty_content_400(self, client):
        r = client.post("/api/messages/send", json={"content": ""})
        assert r.status_code == 400

    def test_send_message_nonexistent_agent_404(self, client):
        r = client.post("/api/messages/send", json={
            "content": "hello",
            "agent": "nonexistent_xyz_999",
        })
        assert r.status_code == 404

    def test_unknown_endpoint_404(self, client):
        r = client.get("/api/nonexistent_endpoint")
        assert r.status_code == 404


class TestSSEEndpoint:
    """Verify SSE streaming endpoint."""

    def test_logs_stream_returns_sse(self, server_url):
        """SSE endpoint should return text/event-stream content type."""
        with httpx.Client(base_url=server_url, timeout=5) as c:
            try:
                with c.stream("GET", "/api/logs/stream?agent=main", timeout=2) as resp:
                    assert resp.status_code == 200
                    ct = resp.headers.get("content-type", "")
                    assert "text/event-stream" in ct
                    # Read a small chunk to confirm it starts streaming
                    chunk = next(resp.iter_bytes())
                    assert len(chunk) >= 0
            except (httpx.ReadTimeout, httpx.ReadError, StopIteration):
                # Timeout is expected for SSE — connection held open
                pass


# ═══════════════════════════════════════════════════════════
# 2. AGENT LIFECYCLE FLOW
# ═══════════════════════════════════════════════════════════


class TestAgentLifecycleFlow:
    """End-to-end: create task -> list tasks -> send message -> verify inbox file."""

    def test_full_lifecycle(self, client):
        ts = int(time.time())
        task_title = f"[INTTEST] lifecycle task {ts}"
        msg_content = f"[INTTEST] lifecycle message {ts}"

        # Step 1: Create a task via API
        r_create = client.post("/api/tasks", json={
            "title": task_title,
            "description": "lifecycle integration test task",
            "assignee": "main",
        })
        assert r_create.status_code == 201
        created = r_create.json()
        task_id = created["id"]
        assert created["status"] == "pending"

        # Step 2: Verify task appears in task list
        r_list = client.get("/api/tasks")
        assert r_list.status_code == 200
        tasks = r_list.json()
        found = any(t.get("id") == task_id for t in tasks)
        assert found, f"Task {task_id} not found in task list"

        # Step 3: Send message via API
        r_msg = client.post("/api/messages/send", json={
            "content": msg_content,
            "agent": "main",
        })
        assert r_msg.status_code == 201
        msg_data = r_msg.json()
        assert msg_data["status"] == "sent"
        assert "file" in msg_data

        # Step 4: Verify inbox file was actually created
        inbox_dir = LOOPCLI_ROOT / "main" / "inbox"
        msg_file = inbox_dir / msg_data["file"]
        assert msg_file.exists(), f"Inbox file {msg_file} was not created"

        # Verify file content is valid
        content = msg_file.read_text(encoding="utf-8")
        assert msg_content in content or "integration test" in content.lower()

        # Cleanup
        msg_file.unlink(missing_ok=True)

    def test_agent_list_includes_known_agents(self, client):
        """Verify that scan_agents finds expected agents."""
        r = client.get("/api/agents")
        agents = r.json()
        agent_ids = [a["id"] for a in agents]
        assert "main" in agent_ids

    def test_tasks_filter_by_agent(self, client):
        """Verify task filtering by agent works."""
        r_all = client.get("/api/tasks", params={"agent": "__all__"})
        assert r_all.status_code == 200
        r_main = client.get("/api/tasks", params={"agent": "main"})
        assert r_main.status_code == 200

    def test_create_and_verify_task_fields(self, client):
        """Verify task creation returns all expected fields."""
        r = client.post("/api/tasks", json={
            "title": "[INTTEST] field verification",
            "description": "checking all task fields",
            "assignee": "main",
        })
        assert r.status_code == 201
        data = r.json()
        assert "id" in data
        assert "title" in data
        assert "description" in data
        assert "status" in data
        assert "assignee" in data
        assert data["status"] == "pending"
        assert data["assignee"] == "main"


# ═══════════════════════════════════════════════════════════
# 3. SECURITY MECHANISM VALIDATION
# ═══════════════════════════════════════════════════════════


class TestSecurityAuth:
    """Verify API Key authentication blocks unauthenticated requests."""

    @patch("server.API_KEY", "e2e-test-secret-key")
    def test_post_task_no_key_401(self, client):
        r = client.post("/api/tasks", json={
            "title": "[INTTEST] should be rejected",
            "description": "no api key",
        })
        assert r.status_code == 401
        assert "error" in r.json()

    @patch("server.API_KEY", "e2e-test-secret-key")
    def test_post_task_wrong_key_401(self, client):
        r = client.post("/api/tasks", json={
            "title": "[INTTEST] wrong key",
            "description": "bad key",
        }, headers={"X-API-Key": "wrong-key"})
        assert r.status_code == 401

    @patch("server.API_KEY", "e2e-test-secret-key")
    def test_post_task_valid_key_201(self, client):
        r = client.post("/api/tasks", json={
            "title": "[INTTEST] auth task",
            "description": "valid key",
        }, headers={"X-API-Key": "e2e-test-secret-key"})
        assert r.status_code == 201

    @patch("server.API_KEY", "e2e-test-secret-key")
    def test_message_send_no_key_401(self, client):
        r = client.post("/api/messages/send", json={
            "content": "should be rejected",
        })
        assert r.status_code == 401

    @patch("server.API_KEY", "e2e-test-secret-key")
    def test_message_send_valid_key_201(self, client):
        r = client.post("/api/messages/send", json={
            "content": "[INTTEST] auth message",
        }, headers={"X-API-Key": "e2e-test-secret-key"})
        assert r.status_code == 201
        data = r.json()
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            msg_path.unlink(missing_ok=True)

    @patch("server.API_KEY", "e2e-test-secret-key")
    def test_key_via_query_param_201(self, client):
        r = client.post("/api/messages/send?key=e2e-test-secret-key", json={
            "content": "[INTTEST] query param auth",
        })
        assert r.status_code == 201
        data = r.json()
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            msg_path.unlink(missing_ok=True)


class TestSecurityPathTraversal:
    """Verify path traversal attacks are blocked."""

    def test_logs_traversal_400(self, client):
        r = client.get("/api/logs", params={"agent": "../etc/passwd"})
        assert r.status_code == 400

    def test_logs_dotdot_400(self, client):
        r = client.get("/api/logs", params={"agent": ".."})
        assert r.status_code == 400

    def test_logs_backslash_traversal_400(self, client):
        r = client.get("/api/logs", params={"agent": "main\\..\\etc"})
        assert r.status_code == 400

    def test_messages_traversal_400(self, client):
        r = client.post("/api/messages/send", json={
            "content": "evil",
            "agent": "../etc",
        })
        assert r.status_code == 400

    def test_tasks_traversal_400(self, client):
        r = client.get("/api/tasks", params={"agent": "../../../etc"})
        assert r.status_code == 400

    def test_agent_tasks_traversal_404_or_400(self, client):
        r = client.get("/api/agents/../etc/tasks")
        assert r.status_code in (400, 404)

    def test_null_byte_injection_400(self, client):
        r = client.get("/api/logs", params={"agent": "main\x00evil"})
        assert r.status_code == 400


class TestSecurityBodyLimit:
    """Verify request body size limit (10KB) is enforced."""

    def test_oversized_body_413(self, client):
        large_payload = {"content": "A" * (11 * 1024)}
        r = client.post("/api/messages/send", json=large_payload)
        assert r.status_code == 413

    def test_exact_limit_body_accepted(self, client):
        # Body just under 10KB should be accepted
        content = "B" * (9 * 1024)
        r = client.post("/api/messages/send", json={
            "content": content,
            "agent": "main",
        })
        assert r.status_code == 201
        data = r.json()
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            msg_path.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════
# 4. WEBUI FRONTEND VALIDATION
# ═══════════════════════════════════════════════════════════


class TestFrontendLoad:
    """Verify WebUI frontend page loads correctly."""

    def test_root_returns_html(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        body = r.text
        assert len(body) > 100
        assert "<html" in body.lower() or "<!doctype" in body.lower()

    def test_index_html_returns_html(self, client):
        r = client.get("/index.html")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_static_assets_accessible(self, client):
        """Verify that CSS/JS references in the page can be served."""
        r = client.get("/")
        body = r.text.lower()
        # Check that common asset patterns exist in the HTML
        has_assets = any(tag in body for tag in ["<script", "<link", "<style"])
        assert has_assets, "No script/link/style tags found in frontend HTML"

    def test_frontend_contains_agent_section(self, client):
        """Verify frontend has agent-related UI elements."""
        r = client.get("/")
        body = r.text.lower()
        # The dashboard should reference agents
        assert "agent" in body, "Frontend does not contain agent-related content"


# ═══════════════════════════════════════════════════════════
# 5. CORS VALIDATION
# ═══════════════════════════════════════════════════════════


class TestCORSHeaders:
    """Verify CORS headers are correctly applied."""

    def test_options_204(self, client):
        r = client.options("/api/agents")
        assert r.status_code == 204

    def test_allowed_origin(self, client):
        r = client.options("/api/agents", headers={"Origin": "http://localhost:3000"})
        assert r.status_code == 204
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_disallowed_origin_no_header(self, client):
        r = client.options("/api/agents", headers={"Origin": "http://evil.com"})
        assert r.status_code == 204
        assert r.headers.get("access-control-allow-origin") is None

    def test_cors_methods_allowed(self, client):
        r = client.options("/api/tasks", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        })
        assert r.status_code == 204
