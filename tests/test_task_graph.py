"""Tests for P4 task graph readiness and dispatch."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_store import ArtifactStore
from task_graph import (
    build_graph,
    next_task,
    parse_task,
    readiness,
    validate,
)
from tests.helpers import seeded_store


def _task_content(title: str, status: str = "proposed", priority: str = "1", deps: str = ""):
    return (
        f"## id\ntasks/x\n## title\n{title}\n## acceptance\n{title} works\n"
        f"## status\n{status}\n## priority\n{priority}\n## depends_on\n{deps}\n"
    )


class ParseTaskTest(unittest.TestCase):
    def test_parse_falls_back_on_bad_status(self):
        task = parse_task("tasks/x", _task_content("x", status="bogus"))
        self.assertEqual(task.status, "proposed")

    def test_parse_falls_back_on_bad_priority(self):
        task = parse_task("tasks/x", _task_content("x", priority="high"))
        self.assertEqual(task.priority, 999)

    def test_parse_deps(self):
        task = parse_task("tasks/x", _task_content("x", deps="tasks/a, tasks/b"))
        self.assertIn("tasks/a", task.depends_on)
        self.assertIn("tasks/b", task.depends_on)


class TaskGraphTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = seeded_store(Path(self.tmp.name))

    def _add(self, task_id, content):
        self.store.write(task_id, "tasks", content, status="accepted")

    def test_build_graph(self):
        graph = build_graph(self.store)
        self.assertIn("tasks/auth-01", graph["nodes"])

    def test_readiness_missing_dep(self):
        dep = "tasks/blocker"
        self._add("tasks/two", _task_content("two", deps=dep))
        ready = readiness(self.store)
        self.assertIn(dep, ready["tasks/two"]["missing_deps"])
        self.assertFalse(ready["tasks/two"]["ready"])

    def test_next_task_picks_ready_highest_priority(self):
        # Use an isolated store so the seeded auth-01 task does not also compete.
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            store.init()
            store.write("tasks/low", "tasks", _task_content("low", priority="9"), status="accepted")
            store.write("tasks/high", "tasks", _task_content("high", priority="1"), status="accepted")
            nxt = next_task(store)
        self.assertEqual(nxt["task"], "tasks/high")
        self.assertIn("reason", nxt)

    def test_next_task_none_when_all_done(self):
        self._add("tasks/auth-01", _task_content("auth-01", status="done"))
        self.assertIsNone(next_task(self.store))

    def test_validate_done_without_acceptance(self):
        self._add("tasks/x", "## id\ntasks/x\n## title\nx\n## status\ndone\n## priority\n1\n")
        issues = validate(self.store)
        self.assertTrue(any("missing acceptance" in i for i in issues))

    def test_validate_unknown_dep(self):
        self._add("tasks/x", _task_content("x", deps="tasks/nope"))
        issues = validate(self.store)
        self.assertTrue(any("unknown task" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
