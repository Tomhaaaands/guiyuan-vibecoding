"""Regression tests for the VCM internal module protocol and intent router."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.vcm_core.module_protocol import ModuleResult, blocked, complete
from tools.vcm_workflow.orchestrator import route_intent, run_route


class ModuleProtocolTest(unittest.TestCase):
    def test_envelope_has_stable_fields_and_version(self):
        result = complete("requirement", artifacts=["REQ-1"], evidence=[{"source": "test"}])
        self.assertEqual(
            set(result),
            {"module_id", "contract_version", "status", "artifacts", "evidence", "blockers", "next_action"},
        )
        self.assertEqual(result["contract_version"], "v1")
        self.assertEqual(result["status"], "complete")

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            ModuleResult("qa", "unknown")

    def test_blocked_carries_action(self):
        result = blocked("planning", ["missing acceptance"], next_action="补充验收")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blockers"], ["missing acceptance"])
        self.assertEqual(result["next_action"], "补充验收")


class WorkflowRouterTest(unittest.TestCase):
    def test_routes_by_responsibility(self):
        self.assertEqual(route_intent("请分析需求和验收范围"), "requirement")
        self.assertEqual(route_intent("拆任务并检查依赖"), "planning")
        self.assertEqual(route_intent("跑测试并回归"), "qa")
        self.assertEqual(route_intent("准备 GitHub release"), "release")
        self.assertEqual(route_intent("做一个界面设计"), "workflow")

    def test_lifecycle_routes_return_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_route(Path(tmp), "请做一次发布准备")
        self.assertEqual(result["route"], "release")
        self.assertEqual(result["contract_version"], "v1")
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
