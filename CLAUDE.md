# Prompt Optimizer Lite Project Guide

## Deletion Safety

禁止批量删除文件或目录。

不要使用：

- `del /s`
- `rd /s`
- `rmdir /s`
- `Remove-Item -Recurse`
- `rm -rf`

需要删除文件时，只能一次删除一个明确路径的文件。

正确示例：

```bash
rm "/Users/user/path/to/file.txt"
```

如果需要批量删除文件，应停止操作，并向用户请求，让用户手动删除。
即使用户授予 full access，也必须遵守以上删除限制。

## Prompt Optimizer Experience

When the user starts a message with `/promptopt`, `promptopt`, `promptopt:`, `PromptOpt`, or asks to optimize and run a prompt, behave like the PromptOpt app adapter. Treat this as a packaged app/tool behavior, not as a markdown-file workflow. Do not mention `.md` command files to the user.

Use this project command as the style guide when useful:

```bash
bin/prompt-optimizer-lite render-prompt "<raw prompt>"
```

Then produce the optimized prompt yourself. Do not return the rendered few-shot request as the final answer.

Always show:

1. `## Prompt Optimizer 预览`
2. The original prompt, optimized prompt, and route
3. `## 执行结果`
4. The answer produced by executing the optimized prompt

````markdown
## Prompt Optimizer 预览

### 原始 Prompt

```text
<raw prompt>
```

### 优化后的 Prompt

```text
<optimized prompt>
```

### 优化路由

`Claude Code project adapter`

---

## 执行结果

<answer produced by executing the optimized prompt>
````

Only skip execution when the user explicitly says "只优化", "不要执行", "preview only", or equivalent.
