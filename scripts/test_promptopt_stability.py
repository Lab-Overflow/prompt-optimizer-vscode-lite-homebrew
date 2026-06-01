#!/usr/bin/env python3

from __future__ import annotations

import sys
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import local_model_manager as manager  # noqa: E402


SAMPLES = [
    "设计一个产品发布计划",
    "帮我写一个客户成功团队的季度复盘模板",
    "把一个模糊的创业想法整理成商业计划 prompt",
    "为一个 AI 编程工具写官网首页文案",
    "写一个团队周会总结生成器提示词",
    "帮我规划一个用户调研访谈大纲",
    "生成一个新员工 onboarding 计划",
    "把 PRD 草稿优化成工程可执行任务",
    "写一个 API 文档审查 prompt",
    "帮我设计一个知识库迁移方案",
    "请作为红队审查这个产品发布计划",
    "红队审稿：我们的产品功能越多越好，用户自然会喜欢",
    "review this GTM plan and list fatal assumptions",
    "找出这份商业计划里的漏洞和风险",
    "批判性审查这段融资 pitch",
    "对这份技术方案做安全和可行性审查",
    "审查一篇论文摘要中的逻辑跳跃",
    "帮我做一次逆向评审，专门挑错",
    "找出这份路线图的执行风险",
    "以审稿人身份指出这段文案的误导点",
    "帮我回复客户的砍价消息，商品是二手相机",
    "生成一个客服回复模板，包含 {{name}} 和 {{order_id}}",
    "把销售跟进话术做成变量模板",
    "为批量邮件生成可复用 prompt，占位符包括公司和岗位",
    "闲鱼买家压价，帮我写客气但坚定的回复",
    "请提取变量并生成招聘邀约模板",
    "把售后道歉消息整理成客服变量化模板",
    "生成一个多语言客服回复模板",
    "帮我把社群欢迎语做成可复用模板",
    "variable prompt for outbound sales email",
    "画一座漂浮在夜空中的图书馆",
    "文生图：未来城市里的雨夜便利店",
    "生成一张赛博朋克风格的猫咪海报",
    "text to image prompt: ancient library in the clouds",
    "帮我写一个电影感人物肖像的图像提示词",
    "画一个白色机器人在森林里读诗",
    "图像 prompt：低角度拍摄的红色跑车",
    "为游戏场景生成概念图提示词",
    "Seedream prompt: floating island with waterfalls",
    "生成一个儿童绘本风格的插画提示词",
    "build a customer support chatbot prompt",
    "write a prompt for summarizing meeting transcripts",
    "create a coding-agent task prompt for refactoring a module",
    "design a research assistant prompt",
    "turn notes into a polished project brief",
    "make a prompt for analyzing CSV sales data",
    "write a prompt to generate a compliance checklist",
    "create a prompt for planning a conference talk",
    "make a prompt for comparing three vendors",
    "write a prompt for generating release notes",
    "帮我把需求拆成开发任务并给出验收标准",
    "为一个博客选题生成内容大纲 prompt",
    "写一个可执行的用户增长实验设计 prompt",
    "帮我生成一个数据分析报告 prompt",
    "把客服质检规则整理成提示词",
    "设计一个远程团队沟通规范 prompt",
    "生成一个播客访谈问题列表",
    "帮我写一个代码 review 指令",
    "为学生作业反馈生成 prompt",
    "设计一个品牌命名头脑风暴 prompt",
]


class PromptOptStabilityTests(unittest.TestCase):
    def test_many_inputs_render_without_crashing(self) -> None:
        self.assertGreaterEqual(len(SAMPLES), 50)
        for raw in SAMPLES:
            with self.subTest(raw=raw):
                rendered = manager.build_inference_prompt(raw, "auto")
                self.assertIn("# 系统要求", rendered)
                self.assertIn("# 待优化需求", rendered)
                self.assertIn(raw, rendered)
                self.assertTrue(rendered.endswith("优化后的提示词：\n"))
                self.assertNotIn("<|im_start|>", rendered)
                self.assertNotIn("<|im_end|>", rendered)

    def test_auto_template_classification_is_stable(self) -> None:
        expected = {
            "请作为红队审查这个产品发布计划": "review",
            "帮我回复客户的砍价消息，商品是二手相机": "variables",
            "画一座漂浮在夜空中的图书馆": "text2image",
            "设计一个产品发布计划": "general",
        }
        for raw, template in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(manager.classify_template(raw), template)

    def test_agent_response_contract_order(self) -> None:
        skeleton = """## Prompt Optimizer 预览

### 原始 Prompt

```text
{raw}
```

### 优化后的 Prompt

```text
{optimized}
```

### 优化路由

`Codex project adapter`

---

## 执行结果

{result}
"""
        for raw in SAMPLES:
            with self.subTest(raw=raw):
                text = skeleton.format(raw=raw, optimized="optimized prompt", result="execution result")
                preview = text.index("## Prompt Optimizer 预览")
                original = text.index("### 原始 Prompt", preview)
                optimized = text.index("### 优化后的 Prompt", original)
                route = text.index("### 优化路由", optimized)
                result = text.index("## 执行结果", route)
                self.assertLess(preview, original)
                self.assertLess(original, optimized)
                self.assertLess(optimized, route)
                self.assertLess(route, result)

    def test_short_cli_facade_looks_like_app_command(self) -> None:
        completed = subprocess.run(
            [str(ROOT / "bin" / "promptopt"), "--no-animation"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("PromptOpt", completed.stdout)
        self.assertIn("promptopt install-extension", completed.stdout)
        self.assertNotIn("promptopt.md", completed.stdout)


if __name__ == "__main__":
    unittest.main()
