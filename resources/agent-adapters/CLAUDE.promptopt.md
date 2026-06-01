<!-- promptopt:begin -->
## PromptOpt App Adapter

When the user starts a message with `@promptopt`, `/promptopt`, `promptopt`, `promptopt:`, or `PromptOpt`, treat the remaining text as the raw prompt and provide the PromptOpt app experience.

Workflow:

1. Use the bundled PromptOpt CLI as a style guide when useful:

```bash
{{PROMPTOPT_CLI}} render-prompt "<raw prompt>"
```

2. Do not paste the rendered few-shot request as the final answer.
3. Optimize the raw prompt internally and execute the optimized prompt in the same response.
4. Always display sections in this exact order:
   - `## Prompt Optimizer 预览`
   - `### 原始 Prompt`
   - `### 优化后的 Prompt`
   - `### 优化路由`
   - `## 执行结果`
5. Only skip execution when the user explicitly says "只优化", "不要执行", "preview only", or equivalent.
6. Treat this as packaged app behavior. Do not mention adapter files to the user.
<!-- promptopt:end -->
