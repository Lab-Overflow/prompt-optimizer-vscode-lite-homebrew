PromptOpt app command: optimize the user's raw prompt using Prompt Optimizer Lite conventions, then execute the optimized prompt in the same response.

Raw prompt:

```text
$ARGUMENTS
```

Instructions:

1. Use the local project templates as the style guide. If tool use is available, run:

```bash
bin/prompt-optimizer-lite render-prompt "$ARGUMENTS"
```

2. Do not return the rendered few-shot request. Use it to create the optimized prompt.
3. Execute the optimized prompt immediately.
4. Put the prompt preview before the execution result.
5. Only skip execution when the user explicitly says "只优化", "不要执行", "preview only", or equivalent.
6. Output exactly this shape:

````markdown
## Prompt Optimizer 预览

### 原始 Prompt

```text
$ARGUMENTS
```

### 优化后的 Prompt

```text
<optimized prompt>
```

### 优化路由

`Claude Code /promptopt command`

---

## 执行结果

<answer produced by executing the optimized prompt>
````

Do not make the user send the optimized prompt again.
