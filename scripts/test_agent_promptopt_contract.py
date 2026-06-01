#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_FILES = [
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / ".claude" / "commands" / "promptopt.md",
]


class AgentPromptOptContractTests(unittest.TestCase):
    def test_preview_comes_before_execution_result(self) -> None:
        for path in CONTRACT_FILES:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                preview = text.index("## Prompt Optimizer 预览")
                original = text.index("### 原始 Prompt", preview)
                optimized = text.index("### 优化后的 Prompt", original)
                route = text.index("### 优化路由", optimized)
                result = text.index("## 执行结果", route)
                self.assertLess(preview, original)
                self.assertLess(original, optimized)
                self.assertLess(optimized, route)
                self.assertLess(route, result)

    def test_no_expandable_preview_contract_remains(self) -> None:
        forbidden = ("<details>", "</details>", "执行结果 first", "Return the execution result first")
        for path in CONTRACT_FILES:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                for marker in forbidden:
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
