<!-- promptopt:begin -->
PromptOpt app command: optimize the user's raw prompt, then execute the optimized prompt in the same response.

Raw prompt:

```text
$ARGUMENTS
```

Instructions:

1. Use PromptOpt conventions to improve the raw prompt internally.
2. Do not return a rendered few-shot request as the final answer.
3. Execute the optimized prompt immediately.
4. Output sections in this exact order:
   - `## Prompt Optimizer 预览`
   - `### 原始 Prompt`
   - `### 优化后的 Prompt`
   - `### 优化路由`
   - `## 执行结果`
5. Only skip execution when the user explicitly says "只优化", "不要执行", "preview only", or equivalent.
6. Treat this as packaged app behavior. Do not mention adapter files to the user.
<!-- promptopt:end -->
