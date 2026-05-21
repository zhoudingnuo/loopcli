"""
Tests for run.py — agent discovery, task management, and helper functions.
"""

import json
import os
import sys
import threading
import pytest

# run.py calls parser.parse_args() at module level, so we must
# provide valid argv before importing. "list" is a safe no-side-effect command.
_original_argv = sys.argv.copy()
sys.argv = ["run.py", "list"]
sys.path.insert(0, r"D:\loopcli")
from run import (
    get_agent_marker,
    is_agent_enabled,
    discover_agents,
    find_template,
    load_agent_state,
    load_agent_tasks,
    cmd_task_inner,
    LOOPCLI_DIR,
    AGENT_MARKER,
)
sys.argv = _original_argv

from pathlib import Path


# ─── Fixtures ───

@pytest.fixture
def fake_agent(tmp_path):
    """Create a minimal fake agent directory for testing."""
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / AGENT_MARKER).write_text("type: main\n", encoding="utf-8")
    mem_dir = agent_dir / "memory"
    mem_dir.mkdir()
    (mem_dir / "state.json").write_text(json.dumps({
        "agent": "test-agent",
        "status": "idle",
        "run_count": 0,
    }), encoding="utf-8")
    (mem_dir / "tasks.json").write_text("[]", encoding="utf-8")
    log_dir = agent_dir / "log"
    log_dir.mkdir()
    return agent_dir


# ─── get_agent_marker ───

class TestGetAgentMarker:
    def test_reads_valid_marker(self, fake_agent):
        content = get_agent_marker(str(fake_agent))
        assert content == "type: main"

    def test_returns_none_for_missing(self, tmp_path):
        assert get_agent_marker(str(tmp_path / "nonexistent")) is None

    def test_reads_disabled_marker(self, tmp_path):
        d = tmp_path / "disabled-agent"
        d.mkdir()
        (d / AGENT_MARKER).write_text("type: main\ndisabled: true\n", encoding="utf-8")
        content = get_agent_marker(str(d))
        assert "disabled" in content


# ─── is_agent_enabled ───

class TestIsAgentEnabled:
    def test_enabled_agent(self, fake_agent):
        assert is_agent_enabled(str(fake_agent)) is True

    def test_disabled_agent(self, tmp_path):
        d = tmp_path / "disabled"
        d.mkdir()
        (d / AGENT_MARKER).write_text("type: main\ndisabled: true\n", encoding="utf-8")
        assert is_agent_enabled(str(d)) is False

    def test_no_marker(self, tmp_path):
        assert is_agent_enabled(str(tmp_path)) is False


# ─── discover_agents ───

class TestDiscoverAgents:
    def test_finds_real_agents(self):
        agents = discover_agents()
        assert isinstance(agents, list)
        # main should always be discovered
        names = [a["name"] for a in agents]
        assert "main" in names

    def test_agent_has_required_keys(self):
        agents = discover_agents()
        for a in agents:
            assert "name" in a
            assert "path" in a

    def test_excludes_disabled(self):
        # discover_agents() without include_disabled should skip disabled agents
        agents = discover_agents(include_disabled=False)
        # Verify none of the returned agents are disabled
        for a in agents:
            assert is_agent_enabled(a["path"])


# ─── find_template ───

class TestFindTemplate:
    def test_existing_template(self):
        result = find_template("engineering-frontend-developer")
        if result:
            assert result.endswith("engineering-frontend-developer.md")
            assert os.path.isfile(result)

    def test_nonexistent_template(self):
        result = find_template("nonexistent-template-xyz-999")
        assert result is None


# ─── load_agent_state ───

class TestLoadAgentState:
    def test_loads_main_state(self):
        main_dir = os.path.join(LOOPCLI_DIR, "main")
        state = load_agent_state(main_dir)
        assert state is not None
        assert state.get("agent", "").lower() == "main"

    def test_loads_state_from_fixture(self, fake_agent):
        state = load_agent_state(str(fake_agent))
        assert state["agent"] == "test-agent"
        assert state["status"] == "idle"

    def test_missing_state_returns_none(self, tmp_path):
        assert load_agent_state(str(tmp_path)) is None


# ─── load_agent_tasks ───

class TestLoadAgentTasks:
    def test_loads_tasks(self, fake_agent):
        tasks = load_agent_tasks(str(fake_agent))
        assert isinstance(tasks, list)

    def test_empty_tasks(self, fake_agent):
        tasks = load_agent_tasks(str(fake_agent))
        assert tasks == []

    def test_missing_returns_empty(self, tmp_path):
        tasks = load_agent_tasks(str(tmp_path))
        assert tasks == []

    def test_real_main_tasks(self):
        main_dir = os.path.join(LOOPCLI_DIR, "main")
        tasks = load_agent_tasks(main_dir)
        assert isinstance(tasks, list)


# ─── cmd_task_inner ───

class TestCmdTaskInner:
    def test_adds_task_to_fake_agent_exits(self, fake_agent):
        """cmd_task_inner expects agent in LOOPCLI_DIR, not tmp_path."""
        with pytest.raises(SystemExit):
            cmd_task_inner("test-agent", "Test task title", "Test description")

    def test_adds_task_to_real_agent(self):
        """Test adding a task to the real engineering-frontend-developer agent."""
        agent_name = "engineering-frontend-developer"
        agent_dir = os.path.join(LOOPCLI_DIR, agent_name)
        if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
            pytest.skip("Agent not found")

        tasks_before = load_agent_tasks(agent_dir)
        count_before = len(tasks_before)

        try:
            cmd_task_inner(agent_name, "[TEST] unit test task", "[TEST] desc")

            tasks_after = load_agent_tasks(agent_dir)
            assert len(tasks_after) == count_before + 1

            new_task = tasks_after[-1]
            assert new_task["title"] == "[TEST] unit test task"
            assert new_task["status"] == "pending"
        finally:
            with open(os.path.join(agent_dir, "memory", "tasks.json"), "w", encoding="utf-8") as f:
                json.dump(tasks_before, f, indent=2, ensure_ascii=False)

    def test_task_id_auto_increments(self):
        agent_name = "engineering-frontend-developer"
        agent_dir = os.path.join(LOOPCLI_DIR, agent_name)
        if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
            pytest.skip("Agent not found")

        tasks_before = load_agent_tasks(agent_dir)
        max_id = max((t["id"] for t in tasks_before), default=0)

        try:
            cmd_task_inner(agent_name, "[TEST] increment test", "")

            tasks_after = load_agent_tasks(agent_dir)
            new_task = tasks_after[-1]
            assert new_task["id"] == max_id + 1
        finally:
            with open(os.path.join(agent_dir, "memory", "tasks.json"), "w", encoding="utf-8") as f:
                json.dump(tasks_before, f, indent=2, ensure_ascii=False)


# ─── Integration: agent directory structure ───

class TestAgentStructure:
    def test_main_has_required_files(self):
        main_dir = Path(LOOPCLI_DIR) / "main"
        assert (main_dir / AGENT_MARKER).exists()
        assert (main_dir / "memory" / "state.json").exists()
        assert (main_dir / "memory" / "tasks.json").exists()

    def test_frontend_agent_has_required_files(self):
        agent_dir = Path(LOOPCLI_DIR) / "engineering-frontend-developer"
        if not (agent_dir / AGENT_MARKER).exists():
            pytest.skip("Agent not found")
        assert (agent_dir / "SOUL.md").exists()
        assert (agent_dir / "memory" / "state.json").exists()
        assert (agent_dir / "memory" / "tasks.json").exists()


# ─── File lock mechanism ───

class TestFileLock:
    """Tests that verify msvcrt file locking prevents data corruption."""

    def _locked_state_update(self, state_file):
        """Simulates the state update logic from run_agent with file locking."""
        import msvcrt
        with open(state_file, "r+") as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            try:
                state = json.load(f)
                state["run_count"] = state.get("run_count", 0) + 1
                f.seek(0)
                f.truncate()
                json.dump(state, f, indent=2, ensure_ascii=False)
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

    def test_concurrent_writes_no_corruption(self, tmp_path):
        """Multiple threads updating state concurrently must produce correct result."""
        state_file = str(tmp_path / "state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"run_count": 0}, f)

        N = 10
        barrier = threading.Barrier(N)
        errors = []

        def worker():
            barrier.wait()
            try:
                self._locked_state_update(state_file)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors during concurrent writes: {errors}"
        with open(state_file, encoding="utf-8") as f:
            final = json.load(f)
        assert final["run_count"] == N

    def test_lock_produces_valid_json(self, tmp_path):
        """Even under heavy contention, the output file must be valid JSON."""
        import msvcrt
        state_file = str(tmp_path / "state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"counter": 0}, f)

        N = 10

        def update():
            for _ in range(50):
                try:
                    with open(state_file, "r+") as f:
                        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                        try:
                            state = json.load(f)
                            state["counter"] = state.get("counter", 0) + 1
                            f.seek(0)
                            f.truncate()
                            json.dump(state, f, indent=2, ensure_ascii=False)
                        finally:
                            f.seek(0)
                            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    return
                except OSError:
                    import time as _time
                    _time.sleep(0.01)

        threads = [threading.Thread(target=update) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with open(state_file, encoding="utf-8") as f:
            final = json.load(f)
        assert final["counter"] == N

    def test_single_write_preserves_data(self, tmp_path):
        """A single locked write preserves all existing fields."""
        state_file = str(tmp_path / "state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"agent": "test", "status": "running", "run_count": 5}, f)

        self._locked_state_update(state_file)

        with open(state_file, encoding="utf-8") as f:
            final = json.load(f)
        assert final["agent"] == "test"
        assert final["status"] == "running"
        assert final["run_count"] == 6
