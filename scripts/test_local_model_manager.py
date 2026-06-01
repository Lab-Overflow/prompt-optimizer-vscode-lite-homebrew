#!/usr/bin/env python3

from __future__ import annotations

import io
import os
import stat
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

import local_model_manager as manager


class LocalModelManagerTests(unittest.TestCase):
    def test_classifies_reference_workflows(self) -> None:
        self.assertEqual(manager.classify_template("帮我回复客户的砍价消息"), "variables")
        self.assertEqual(manager.classify_template("请作为红队审查这份发布方案"), "review")
        self.assertEqual(manager.classify_template("画一座漂浮在夜空中的图书馆"), "text2image")
        self.assertEqual(manager.classify_template("帮我规划一个活动"), "general")

    def test_rendered_prompt_contains_selected_few_shot(self) -> None:
        prompt = manager.build_inference_prompt("帮我回复客户，使用 {{name}}", "auto")
        self.assertIn("变量化任务", prompt)
        self.assertIn("{{item}}", prompt)
        self.assertIn("帮我回复客户，使用 {{name}}", prompt)
        self.assertTrue(prompt.endswith("优化后的提示词：\n"))

    def test_status_detects_cached_llama_cpp_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = root / "runtime" / "llama-cli"
            cli.parent.mkdir(parents=True)
            cli.write_text("#!/bin/sh\n", encoding="utf-8")
            cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
            gguf = root / "models" / manager.MODEL_FILENAME
            gguf.parent.mkdir(parents=True)
            with gguf.open("wb") as fh:
                fh.truncate(manager.MIN_MODEL_BYTES)
            with patch.dict(os.environ, {"PROMPT_OPTIMIZER_LITE_HOME": str(root)}, clear=False):
                with patch.object(manager, "_ollama_tags", return_value=[]):
                    with patch.object(manager.shutil, "which", return_value=None):
                        status = manager.get_status()
        self.assertTrue(status["ready"])
        self.assertEqual(status["backend"], "llama.cpp")

    def test_archive_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "runtime.tar.gz"
            payload = b"bad"
            with tarfile.open(archive, "w:gz") as package:
                member = tarfile.TarInfo("../escape")
                member.size = len(payload)
                package.addfile(member, io.BytesIO(payload))
            with self.assertRaisesRegex(RuntimeError, "Unsafe archive member"):
                manager._extract_archive(archive, root / "extract")

    def test_archive_external_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "runtime.tar.gz"
            with tarfile.open(archive, "w:gz") as package:
                member = tarfile.TarInfo("runtime/link")
                member.type = tarfile.SYMTYPE
                member.linkname = "../../escape"
                package.addfile(member)
            with self.assertRaisesRegex(RuntimeError, "Unsafe archive symlink"):
                manager._extract_archive(archive, root / "extract")


if __name__ == "__main__":
    unittest.main()
