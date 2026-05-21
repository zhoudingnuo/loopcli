"""
Tests for webui/server.py — API endpoints and helper functions.
Uses a real threaded HTTP server with httpx client.
"""

import json
import os
import sys
import time
import threading
import pytest
import httpx
from unittest.mock import patch

# Add webui directory to path so we can import server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "webui"))

from server import (
    _safe_agent_path,
    read_json,
    write_json,
    scan_agents,
    get_main_tasks,
    get_recent_lines,
    WebUIHandler,
    ThreadedHTTPServer,
    LOOPCLI_ROOT,
    MAIN_DIR,
)
from pathlib import Path


# ─── Fixtures ───

BASE_PORT = 18765
_port_lock = threading.Lock()
_port_counter = [0]


def _get_port():
    with _port_lock:
        _port_counter[0] += 1
        return BASE_PORT + _port_counter[0]


@pytest.fixture(scope="module")
def http_server():
    """Start a real HTTP server in a thread for the entire module."""
    port = _get_port()
    server = ThreadedHTTPServer(("127.0.0.1", port), WebUIHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture
def client(http_server):
    return httpx.Client(base_url=http_server, timeout=5)


# ─── Helper: _safe_agent_path ───

class TestSafeAgentPath:
    def test_valid_agent(self):
        result = _safe_agent_path("main")
        assert result is not None
        assert result == LOOPCLI_ROOT / "main"

    def test_empty_string(self):
        assert _safe_agent_path("") is None

    def test_slash_traversal(self):
        assert _safe_agent_path("main/../../../etc") is None

    def test_backslash_traversal(self):
        assert _safe_agent_path("main\\..\\..\\etc") is None

    def test_double_dot(self):
        assert _safe_agent_path("..") is None

    def test_path_with_slash(self):
        assert _safe_agent_path("foo/bar") is None

    def test_path_with_backslash(self):
        assert _safe_agent_path("foo\\bar") is None

    def test_valid_subdir_name(self):
        result = _safe_agent_path("engineering-frontend-developer")
        assert result is not None
        assert result.name == "engineering-frontend-developer"

    def test_null_byte_injection(self):
        assert _safe_agent_path("main\x00") is None

    def test_null_byte_in_middle(self):
        assert _safe_agent_path("main\x00evil") is None

    def test_null_byte_at_start(self):
        assert _safe_agent_path("\x00main") is None

    def test_null_byte_with_suffix(self):
        assert _safe_agent_path("main\x00.sh") is None


# ─── Helper: read_json / write_json ───

class TestJsonIO:
    def test_read_nonexistent_returns_default(self, tmp_path):
        result = read_json(tmp_path / "nope.json", {"x": 1})
        assert result == {"x": 1}

    def test_read_nonexistent_no_default(self, tmp_path):
        result = read_json(tmp_path / "nope.json")
        assert result == {}

    def test_read_valid_json(self, tmp_path):
        p = tmp_path / "test.json"
        p.write_text('{"a": 1}', encoding="utf-8")
        assert read_json(p) == {"a": 1}

    def test_read_corrupt_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid", encoding="utf-8")
        assert read_json(p, "fallback") == "fallback"

    def test_write_json_creates_dirs(self, tmp_path):
        p = tmp_path / "sub" / "dir" / "out.json"
        write_json(p, {"k": "v"})
        assert p.exists()
        assert json.loads(p.read_text(encoding="utf-8")) == {"k": "v"}

    def test_roundtrip(self, tmp_path):
        p = tmp_path / "rt.json"
        data = {"hello": "世界", "num": 42}
        write_json(p, data)
        assert read_json(p) == data


# ─── Helper: get_recent_lines ───

class TestGetRecentLines:
    def test_nonexistent_file(self, tmp_path):
        assert get_recent_lines(tmp_path / "nope.log") == []

    def test_reads_last_n(self, tmp_path):
        p = tmp_path / "test.log"
        p.write_text("\n".join(f"line {i}" for i in range(10)), encoding="utf-8")
        lines = get_recent_lines(p, 3)
        assert len(lines) == 3
        assert lines[0] == "line 7"

    def test_all_lines_if_fewer_than_n(self, tmp_path):
        p = tmp_path / "short.log"
        p.write_text("a\nb", encoding="utf-8")
        lines = get_recent_lines(p, 100)
        assert len(lines) == 2


# ─── Helper: scan_agents ───

class TestScanAgents:
    def test_returns_list(self):
        agents = scan_agents()
        assert isinstance(agents, list)

    def test_main_agent_present(self):
        agents = scan_agents()
        names = [a["id"] for a in agents]
        assert "main" in names

    def test_agent_has_required_fields(self):
        agents = scan_agents()
        for a in agents:
            assert "id" in a
            assert "name" in a
            assert "status" in a


# ─── API: GET /api/agents ───

class TestGetAgents:
    def test_returns_200(self, client):
        r = client.get("/api/agents")
        assert r.status_code == 200

    def test_returns_json_list(self, client):
        r = client.get("/api/agents")
        data = r.json()
        assert isinstance(data, list)

    def test_includes_main(self, client):
        r = client.get("/api/agents")
        names = [a["id"] for a in r.json()]
        assert "main" in names


# ─── API: GET /api/tasks ───

class TestGetTasks:
    def test_returns_200(self, client):
        r = client.get("/api/tasks")
        assert r.status_code == 200

    def test_returns_json_list(self, client):
        r = client.get("/api/tasks")
        assert isinstance(r.json(), list)


# ─── API: POST /api/tasks ───

class TestCreateTask:
    def test_create_task_success(self, client):
        tasks_before = client.get("/api/tasks").json()
        try:
            r = client.post("/api/tasks", json={
                "title": f"[TEST] unit test task {time.time()}",
                "description": "created by automated test",
                "assignee": "main",
            })
            assert r.status_code == 201
            data = r.json()
            assert data["status"] == "pending"
            assert data["title"].startswith("[TEST]")
        finally:
            write_json(MAIN_DIR / "memory" / "tasks.json", tasks_before)

    def test_create_task_missing_title(self, client):
        r = client.post("/api/tasks", json={"description": "no title"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_create_task_empty_body(self, client):
        r = client.post("/api/tasks", json={})
        assert r.status_code == 400


# ─── API: POST /api/messages/send ───

class TestMessageSend:
    def test_send_to_main(self, client):
        r = client.post("/api/messages/send", json={
            "content": f"test message {time.time()}",
            "agent": "main",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "sent"
        assert data["agent"] == "main"

        # Cleanup the test message
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            if msg_path.exists():
                msg_path.unlink()

    def test_send_default_agent_is_main(self, client):
        r = client.post("/api/messages/send", json={
            "content": f"default agent test {time.time()}",
        })
        assert r.status_code == 201
        assert r.json()["agent"] == "main"

        # Cleanup
        data = r.json()
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            if msg_path.exists():
                msg_path.unlink()

    def test_send_empty_content(self, client):
        r = client.post("/api/messages/send", json={"content": ""})
        assert r.status_code == 400

    def test_send_to_invalid_agent(self, client):
        r = client.post("/api/messages/send", json={
            "content": "hello",
            "agent": "../etc",
        })
        assert r.status_code == 400

    def test_send_to_nonexistent_agent(self, client):
        r = client.post("/api/messages/send", json={
            "content": "hello",
            "agent": "nonexistent_agent_xyz",
        })
        assert r.status_code == 404


# ─── API: Path traversal rejection ───

class TestPathTraversal:
    def test_agents_endpoint_rejects_traversal(self, client):
        # /api/logs?agent=../etc should be rejected
        r = client.get("/api/logs", params={"agent": "../etc"})
        assert r.status_code == 400

    def test_agents_endpoint_rejects_dotdot(self, client):
        r = client.get("/api/logs", params={"agent": ".."})
        assert r.status_code == 400

    def test_messages_send_rejects_traversal(self, client):
        r = client.post("/api/messages/send", json={
            "content": "test",
            "agent": "../etc",
        })
        assert r.status_code == 400


# ─── API: GET /api/logs ───

class TestGetLogs:
    def test_returns_200(self, client):
        r = client.get("/api/logs")
        assert r.status_code == 200
        data = r.json()
        assert "lines" in data

    def test_with_valid_agent(self, client):
        r = client.get("/api/logs", params={"agent": "main"})
        assert r.status_code == 200

    def test_with_invalid_agent(self, client):
        r = client.get("/api/logs", params={"agent": "../etc"})
        assert r.status_code == 400


# ─── API: OPTIONS (CORS) ───

class TestCORS:
    def test_options_returns_204(self, client):
        r = client.options("/api/agents")
        assert r.status_code == 204

    def test_cors_allows_configured_origin(self, client):
        r = client.options("/api/agents", headers={"Origin": "http://localhost:3000"})
        assert r.status_code == 204
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_rejects_unknown_origin(self, client):
        r = client.options("/api/agents", headers={"Origin": "http://evil.com"})
        assert r.status_code == 204
        assert r.headers.get("access-control-allow-origin") is None


# ─── API: 404 for unknown POST ───

class TestNotFound:
    def test_unknown_post_returns_404(self, client):
        r = client.post("/api/nonexistent")
        assert r.status_code == 404


# ─── API Key authentication ───

class TestApiKeyAuth:
    @patch("server.API_KEY", "test-secret-key-12345")
    def test_create_task_rejects_without_key(self, client):
        r = client.post("/api/tasks", json={
            "title": "[TEST] should be rejected",
            "description": "no api key",
        })
        assert r.status_code == 401
        assert "error" in r.json()

    @patch("server.API_KEY", "test-secret-key-12345")
    def test_create_task_rejects_wrong_key(self, client):
        r = client.post("/api/tasks", json={
            "title": "[TEST] wrong key",
            "description": "bad api key",
        }, headers={"X-API-Key": "wrong-key"})
        assert r.status_code == 401

    @patch("server.API_KEY", "test-secret-key-12345")
    def test_create_task_accepts_valid_key(self, client):
        tasks_before = client.get("/api/tasks").json()
        try:
            r = client.post("/api/tasks", json={
                "title": "[TEST] auth validated task",
                "description": "with correct api key",
            }, headers={"X-API-Key": "test-secret-key-12345"})
            assert r.status_code == 201
            assert r.json()["status"] == "pending"
        finally:
            write_json(MAIN_DIR / "memory" / "tasks.json", tasks_before)

    @patch("server.API_KEY", "test-secret-key-12345")
    def test_message_send_rejects_without_key(self, client):
        r = client.post("/api/messages/send", json={
            "content": "should be rejected",
        })
        assert r.status_code == 401

    @patch("server.API_KEY", "test-secret-key-12345")
    def test_message_send_accepts_valid_key(self, client):
        r = client.post("/api/messages/send", json={
            "content": "auth test message",
        }, headers={"X-API-Key": "test-secret-key-12345"})
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "sent"
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            if msg_path.exists():
                msg_path.unlink()

    @patch("server.API_KEY", "test-secret-key-12345")
    def test_message_send_key_in_query_params(self, client):
        r = client.post("/api/messages/send?key=test-secret-key-12345", json={
            "content": "query param key test",
        })
        assert r.status_code == 201
        data = r.json()
        if data.get("file"):
            msg_path = LOOPCLI_ROOT / "main" / "inbox" / data["file"]
            if msg_path.exists():
                msg_path.unlink()
