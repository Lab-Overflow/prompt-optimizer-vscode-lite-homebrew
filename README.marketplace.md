# Prompt Optimizer Mini

A lightweight VS Code extension that transforms rough ideas into execution-ready prompts with a built-in model router and an optional on-demand local GGUF model.

## Install

### From VS Code Marketplace (Recommended)

Search **"Prompt Optimizer Mini"** in VS Code Extensions, or install via CLI:

```bash
code --install-extension fullstack1ape.prompt-optimizer-mini
```

### From Source

1. Clone and open this repo in VS Code.
2. Install dependencies and compile:

```bash
npm install
npm run compile
python3 -B -m unittest scripts/test_promptopt_stability.py scripts/test_agent_promptopt_contract.py scripts/test_local_model_manager.py
```

3. Press `F5` to launch **Extension Development Host**.

### From Homebrew Tap

After the `v1.0.1` release and tap are published:

```bash
brew tap Lab-Overflow/prompt-optimizer
brew install prompt-optimizer-lite
```

Homebrew installs the lightweight CLI only: no VSIX, Node dependencies, build output, icon assets, or model weights are included. It exposes `promptopt`, `prompt-optimizer-mini`, and `prompt-optimizer-lite`.

Optional VS Code extension install:

```bash
promptopt install-extension
```

### Build and Install VSIX

```bash
npm run package
code --install-extension prompt-optimizer-mini-1.0.1.vsix
```

## Features

- **Zero Configuration** — Install and start optimizing. If no remote model is available, a compact local model can be prepared on demand.
- **Lightweight Package** — Model weights are not bundled in the VSIX.
- **Model Router GUI** — Choose Auto, VS Code Chat, OpenAI-compatible API, Local Model, or Offline Template.
- **Visible Optimization Trace** — Chat and preview views show the optimized prompt plus an expandable before/after route panel.
- **Bring Your Best Model** — Configure your own base URL, API key, and model name. API keys are stored in VS Code SecretStorage.
- **Local GGUF Model** — Reuses Ollama or `llama-cli`, or downloads a `llama.cpp` runtime and the official `Qwen/Qwen3-1.7B-GGUF` `Q8_0` model (about 1.83 GB).
- **Few-Shot Templates** — General, variable-driven, red-team review, and text-to-image prompt patterns are built in.
- **Chat Participant** — Type `@promptopt` in VS Code Chat to optimize prompts conversationally.
- **Editor Command** — Select text and run `Prompt Optimizer Mini: Optimize Prompt` from the command palette, or right-click for the context menu option.
- **Manual Input** — No selection needed. Run the command without selecting text and a prompt input box will appear.
- **Multiple Output Options** — Replace selection, insert at cursor, copy to clipboard, or open as a Markdown preview.
- **Resilient Fallback** — OpenAI-compatible API → VS Code Chat → Local GGUF model → Local Python formatter → Built-in template.
- **Codex / Claude Code Adapters** — Confirm once to add managed workspace adapters, then use `@promptopt ...` in reopened Codex or Claude Code chats.

## How to Use

### Method 1: Chat Participant

Open VS Code Chat and type:

```text
@promptopt Optimize this into an execution-ready prompt: build a customer service chatbot
```

The extension uses the current chat model (Copilot, Codex, Claude, etc.) to optimize your prompt.

### Method 2: Editor Command

1. **With selection**: Select rough prompt text in your editor -> Run `Prompt Optimizer Mini: Optimize Prompt` from command palette (`Ctrl+Shift+P` / `Cmd+Shift+P`), or right-click and select from the context menu.
2. **Without selection**: Run the same command → A prompt input box appears for you to type or paste your rough prompt.
3. Choose an output action:
   - `Replace Selection` — Overwrite the selected text with the optimized prompt
   - `Insert At Cursor` — Insert the optimized prompt at the current cursor position
   - `Copy To Clipboard` — Copy to clipboard for use anywhere
   - `Open Preview` — Open as a Markdown document for review

## Typical Use Cases

- Turn product requirement notes into execution-ready prompts
- Turn coding task ideas into structured coding-agent prompts
- Turn writing outlines into prompts with output format and acceptance criteria
- Turn ambiguous requests into prompts with assumptions, constraints, and verification checks

## Model Router

Use the command palette:

| Command | Purpose |
|---------|---------|
| `Prompt Optimizer Mini: Choose Model Route` | Pick Auto, VS Code Chat, OpenAI-compatible API, Local Model, or Offline Template |
| `Prompt Optimizer Mini: Configure OpenAI-compatible Model` | Save base URL, model name, and API key |
| `Prompt Optimizer Mini: Setup Local Model` | Prepare the local runtime and GGUF before first use |
| `Prompt Optimizer Mini: Show Model Status` | Inspect route and local model readiness |

The default `auto` route uses:

| Priority | Method | When |
|----------|--------|------|
| 1st | OpenAI-compatible API | When configured |
| 2nd | VS Code chat model | When exposed by VS Code extension APIs |
| 3rd | Local GGUF model | Reuses Ollama or `llama-cli`; otherwise prepares runtime and model on demand |
| 4th | Local Python formatter | Fast dependency-free structured fallback |
| 5th | Built-in template | When Python is unavailable |

The local model is the official [`Qwen/Qwen3-1.7B-GGUF`](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF) `Q8_0` file. It is compact enough for common 8 GB Apple Silicon Macs and laptops with 6 GB or more VRAM.

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `promptOptimizerLite.replaceSelection` | boolean | `false` | When `true`, automatically replace selected text with the optimized result. When `false`, show an action picker to choose the output destination. |
| `promptOptimizerLite.fallbackPythonCommand` | string | `""` | Custom Python command for fallback execution (e.g., `/usr/bin/python3`). Leave empty to auto-detect `python3` or `python`. |
| `promptOptimizerLite.modelRoute` | string | `"auto"` | Model router strategy. |
| `promptOptimizerLite.externalBaseUrl` | string | `""` | OpenAI-compatible API base URL. |
| `promptOptimizerLite.externalModel` | string | `""` | OpenAI-compatible model name. |
| `promptOptimizerLite.autoDownloadLocalModel` | boolean | `true` | Prepare local runtime and GGUF on demand. |
| `promptOptimizerLite.localTemplate` | string | `"auto"` | Few-shot template selection. |
| `promptOptimizerLite.showOptimizationTrace` | boolean | `true` | Show original prompt and model route alongside the optimized prompt in chat and preview. |
| `promptOptimizerLite.offerAgentAdapterSetup` | boolean | `true` | Offer to add managed Codex and Claude Code workspace adapters. |

## Requirements

- VS Code `1.105.0` or later
- Python `3.x` for local model bootstrap and local formatter fallback
- Network access during the first local model setup

## Links

- [Source Code](https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew)
- [Report Issues](https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew/issues)
- [License (Apache-2.0)](https://github.com/Lab-Overflow/prompt-optimizer-vscode-lite-homebrew/blob/main/LICENSE)
