#!/usr/bin/env python3

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESOURCE_DIR = ROOT / "resources" / "agent-adapters"
RESOURCES = [
    RESOURCE_DIR / "AGENTS.promptopt.md",
    RESOURCE_DIR / "CLAUDE.promptopt.md",
    RESOURCE_DIR / "promptopt-command.md",
]


class AgentAdapterResourceTests(unittest.TestCase):
    def test_adapter_resources_are_managed_and_ordered(self) -> None:
        expected = [
            "## Prompt Optimizer 预览",
            "### 原始 Prompt",
            "### 优化后的 Prompt",
            "### 优化路由",
            "## 执行结果",
        ]
        for path in RESOURCES:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("<!-- promptopt:begin -->"))
                self.assertTrue(text.rstrip().endswith("<!-- promptopt:end -->"))
                positions = [text.index(marker) for marker in expected]
                self.assertEqual(positions, sorted(positions))

    def test_agent_resources_use_bundled_cli_placeholder(self) -> None:
        for name in ("AGENTS.promptopt.md", "CLAUDE.promptopt.md"):
            with self.subTest(name=name):
                text = (RESOURCE_DIR / name).read_text(encoding="utf-8")
                self.assertIn("{{PROMPTOPT_CLI}}", text)

    def test_extension_exposes_adapter_setup_command(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        commands = {item["command"] for item in package["contributes"]["commands"]}
        activation_events = set(package["activationEvents"])
        settings = package["contributes"]["configuration"]["properties"]
        self.assertIn("promptOptimizerLite.setupAgentAdapters", commands)
        self.assertIn("onCommand:promptOptimizerLite.setupAgentAdapters", activation_events)
        self.assertIn("onStartupFinished", activation_events)
        self.assertIn("promptOptimizerLite.offerAgentAdapterSetup", settings)


if __name__ == "__main__":
    unittest.main()
