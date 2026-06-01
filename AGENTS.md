# Project Instructions

## File Deletion Safety

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

When the user starts a message with `/promptopt`, `promptopt`, `promptopt:`, `PromptOpt`, or asks to optimize and run a prompt, provide the PromptOpt app experience. Treat this as a packaged app/tool behavior, not as a markdown-file workflow. Do not mention `.md` command files to the user.

Workflow:

1. Treat the text after the trigger as the raw prompt.
2. Use the local project templates as the optimization style guide. Prefer running:

```bash
bin/prompt-optimizer-lite render-prompt "<raw prompt>"
```

3. Do not paste the rendered few-shot request as the final answer. Use it to produce the optimized prompt.
4. Immediately execute the optimized prompt in the same response.
5. Always show the prompt preview first: original prompt, optimized prompt, and route.
6. Show the execution result after the preview.
7. Only skip execution when the user explicitly says "只优化", "不要执行", "preview only", or equivalent.

Response format:

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

`Codex project adapter`

---

## 执行结果

<answer produced by executing the optimized prompt>
````

Keep the optimized prompt directly usable, but do not make the user send it again.
