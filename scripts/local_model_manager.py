#!/usr/bin/env python3
"""
Dependency-free local model bootstrap and inference helper.

The extension stays small: this script reuses Ollama or llama-cli when present,
and downloads a llama.cpp runtime plus a compact GGUF model only on demand.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


MODEL_REPO = "Qwen/Qwen3-1.7B-GGUF"
MODEL_VARIANT = "Q8_0"
MODEL_FILENAME = "Qwen3-1.7B-Q8_0.gguf"
MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/main/"
    "Qwen3-1.7B-Q8_0.gguf?download=true"
)
OLLAMA_MODEL = f"hf.co/{MODEL_REPO}:{MODEL_VARIANT}"
LLAMA_CPP_RELEASE_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
MIN_MODEL_BYTES = 500 * 1024 * 1024


def cache_root() -> Path:
    override = os.environ.get("PROMPT_OPTIMIZER_HOME", "").strip() or os.environ.get("PROMPT_OPTIMIZER_LITE_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "prompt-optimizer-mini"
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "prompt-optimizer-mini"
    base = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "prompt-optimizer-mini"


def model_path() -> Path:
    return cache_root() / "models" / MODEL_FILENAME


def templates_path() -> Path:
    return Path(__file__).with_name("few_shot_templates.json")


def load_templates() -> Dict[str, Dict[str, str]]:
    with templates_path().open("r", encoding="utf-8") as fh:
        return json.load(fh)


def classify_template(source: str) -> str:
    lowered = source.lower()
    if any(word in lowered for word in ("文生图", "画一", "绘制", "图片", "图像", "image", "midjourney", "seedream")):
        return "text2image"
    if any(word in lowered for word in ("红队", "审稿", "审查", "review", "漏洞", "风险", "批判")):
        return "review"
    if "{{" in source or any(
        word in lowered
        for word in ("变量", "模板", "批量", "客服", "回复", "砍价", "占位符", "variable")
    ):
        return "variables"
    return "general"


def build_inference_prompt(source: str, template_name: str = "auto") -> str:
    templates = load_templates()
    selected = classify_template(source) if template_name == "auto" else template_name
    if selected not in templates:
        selected = "general"
    example = templates[selected]
    return f"""# 系统要求
你是一位资深 Prompt 工程师。把用户的粗糙需求改写为可以直接交给模型执行的高质量提示词。
必须保留核心意图，补齐必要上下文、约束、输出格式和验收方式。
不要回答原始任务，只输出优化后的提示词正文。默认使用中文。
对简单任务保持简洁；对变量化、审稿和文生图任务使用适合该任务的结构。
/no_think

# “{example['label']}”参考示例

原始需求：
{example['example_input']}

优化后的提示词：
{example['example_output']}

# 待优化需求
只输出下面原始需求对应的优化后提示词正文：
原始需求：
{source.strip()}

优化后的提示词：
"""


def _find_downloaded_llama_cli() -> Optional[Path]:
    executable = "llama-cli.exe" if os.name == "nt" else "llama-cli"
    runtime_dir = cache_root() / "runtime"
    if not runtime_dir.exists():
        return None
    matches = sorted(runtime_dir.rglob(executable))
    return matches[-1] if matches else None


def find_llama_cli() -> Optional[Path]:
    configured = (
        os.environ.get("PROMPT_OPTIMIZER_LLAMA_CLI", "").strip()
        or os.environ.get("PROMPT_OPTIMIZER_LITE_LLAMA_CLI", "").strip()
    )
    if configured and Path(configured).expanduser().is_file():
        return Path(configured).expanduser()
    from_path = shutil.which("llama-cli")
    if from_path:
        return Path(from_path)
    return _find_downloaded_llama_cli()


def _ollama_tags() -> List[str]:
    try:
        request = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(request, timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
    except (OSError, ValueError, urllib.error.URLError):
        return []


def find_ollama_model() -> Optional[str]:
    names = _ollama_tags()
    for name in names:
        if name == OLLAMA_MODEL:
            return name
    for name in names:
        lowered = name.lower()
        if any(
            hint in lowered
            for hint in ("qwen3:1.7b", "qwen3:0.6b", "qwen2.5:1.5b", "llama3.2:1b", "gemma3:1b")
        ):
            return name
    return None


def model_is_ready() -> bool:
    path = model_path()
    return path.is_file() and path.stat().st_size >= MIN_MODEL_BYTES


def get_status() -> Dict[str, Any]:
    ollama_command = shutil.which("ollama")
    ollama_model = find_ollama_model()
    llama_cli = find_llama_cli()
    gguf = model_path()
    if ollama_model:
        backend = "ollama"
        ready = True
    elif llama_cli and model_is_ready():
        backend = "llama.cpp"
        ready = True
    else:
        backend = "missing"
        ready = False
    return {
        "ready": ready,
        "backend": backend,
        "model": ollama_model or (MODEL_FILENAME if model_is_ready() else ""),
        "modelPath": str(gguf),
        "modelDownloaded": model_is_ready(),
        "modelBytes": gguf.stat().st_size if gguf.is_file() else 0,
        "ollamaCommand": ollama_command or "",
        "ollamaModel": ollama_model or "",
        "llamaCli": str(llama_cli) if llama_cli else "",
        "cacheDir": str(cache_root()),
    }


def _report(message: str) -> None:
    print(f"[Prompt Optimizer Mini] {message}", file=sys.stderr, flush=True)


def _download(url: str, destination: Path, label: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "prompt-optimizer-mini"})
    _report(f"Downloading {label}...")
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
        total = int(response.headers.get("Content-Length", "0"))
        downloaded = 0
        last_percent = -1
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if total:
                percent = downloaded * 100 // total
                if percent >= last_percent + 10:
                    _report(f"{label}: {percent}%")
                    last_percent = percent
    partial.replace(destination)


def _archive_suffix() -> str:
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        return "-bin-macos-arm64.tar.gz" if machine in ("arm64", "aarch64") else "-bin-macos-x64.tar.gz"
    if sys.platform.startswith("linux"):
        return "-bin-ubuntu-arm64.tar.gz" if machine in ("arm64", "aarch64") else "-bin-ubuntu-x64.tar.gz"
    if os.name == "nt":
        return "-bin-win-cpu-arm64.zip" if machine in ("arm64", "aarch64") else "-bin-win-cpu-x64.zip"
    raise RuntimeError(f"Unsupported platform for automatic llama.cpp bootstrap: {sys.platform} {machine}")


def _latest_llama_cpp_asset() -> Dict[str, str]:
    request = urllib.request.Request(
        LLAMA_CPP_RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "prompt-optimizer-mini"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    suffix = _archive_suffix()
    for asset in payload.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(suffix):
            return {"name": name, "url": asset["browser_download_url"]}
    raise RuntimeError(f"No llama.cpp release asset found for suffix {suffix}")


def _is_within_directory(directory: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as package:
            for member in package.infolist():
                target = destination / member.filename
                if not _is_within_directory(destination, target):
                    raise RuntimeError(f"Unsafe archive member: {member.filename}")
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise RuntimeError(f"Unsafe archive symlink: {member.filename}")
            package.extractall(destination)
        return
    with tarfile.open(archive, "r:gz") as package:
        for member in package.getmembers():
            target = destination / member.name
            if not _is_within_directory(destination, target):
                raise RuntimeError(f"Unsafe archive member: {member.name}")
            if member.issym():
                link_target = target.parent / member.linkname
                if not _is_within_directory(destination, link_target):
                    raise RuntimeError(f"Unsafe archive symlink: {member.name}")
            elif member.islnk():
                link_target = destination / member.linkname
                if not _is_within_directory(destination, link_target):
                    raise RuntimeError(f"Unsafe archive hardlink: {member.name}")
            elif not (member.isfile() or member.isdir()):
                raise RuntimeError(f"Unsupported archive member: {member.name}")
        package.extractall(destination)


def ensure_llama_cli() -> Path:
    existing = find_llama_cli()
    if existing:
        return existing
    asset = _latest_llama_cpp_asset()
    runtime_dir = cache_root() / "runtime"
    archive = cache_root() / asset["name"]
    _download(asset["url"], archive, "llama.cpp runtime")
    _report("Extracting llama.cpp runtime...")
    _extract_archive(archive, runtime_dir)
    if archive.is_file():
        archive.unlink()
    executable = _find_downloaded_llama_cli()
    if not executable:
        raise RuntimeError("Downloaded llama.cpp runtime does not contain llama-cli")
    if os.name != "nt":
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def ensure_gguf() -> Path:
    path = model_path()
    if model_is_ready():
        return path
    _download(MODEL_URL, path, f"{MODEL_REPO}:{MODEL_VARIANT} model")
    if not model_is_ready():
        raise RuntimeError("Downloaded GGUF model is incomplete")
    return path


def _ollama_pull(command: str) -> Optional[str]:
    _report(f"Pulling {OLLAMA_MODEL} with Ollama...")
    completed = subprocess.run(
        [command, "pull", OLLAMA_MODEL],
        capture_output=True,
        text=True,
        timeout=60 * 30,
        check=False,
    )
    if completed.returncode != 0:
        _report(f"Ollama pull failed: {completed.stderr.strip() or completed.stdout.strip()}")
        return None
    return find_ollama_model() or OLLAMA_MODEL


def ensure_local_model() -> Dict[str, Any]:
    status = get_status()
    if status["ready"]:
        return status
    ollama = status["ollamaCommand"]
    if ollama:
        pulled = _ollama_pull(ollama)
        if pulled:
            refreshed = get_status()
            if not refreshed["ready"]:
                refreshed.update({"ready": True, "backend": "ollama", "ollamaModel": pulled, "model": pulled})
            return refreshed
    ensure_llama_cli()
    ensure_gguf()
    return get_status()


def _strip_model_noise(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = cleaned.replace("<|im_end|>", "").replace("<|im_start|>", "")
    return cleaned.strip()


def _optimize_with_ollama(command: str, model: str, prompt: str) -> str:
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "num_predict": 1536},
        }
    ).encode("utf-8")
    try:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60 * 10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        output = payload.get("message", {}).get("content", "")
    except (OSError, ValueError, urllib.error.URLError):
        completed = subprocess.run(
            [command, "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60 * 10,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "Ollama inference failed")
        output = completed.stdout
    cleaned = _strip_model_noise(output)
    if not cleaned:
        raise RuntimeError("Ollama returned an empty response")
    return cleaned


def _optimize_with_llama_cpp(command: str, gguf: Path, prompt: str) -> str:
    env = dict(os.environ)
    env.setdefault("GGML_LOG_LEVEL", "error")
    completed = subprocess.run(
        [
            command,
            "-m",
            str(gguf),
            "-p",
            prompt,
            "-n",
            "1536",
            "-c",
            "4096",
            "-ngl",
            "99",
            "--temp",
            "0.7",
            "--top-p",
            "0.8",
            "--top-k",
            "20",
            "--no-display-prompt",
        ],
        capture_output=True,
        text=True,
        timeout=60 * 10,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "llama-cli inference failed")
    cleaned = _strip_model_noise(completed.stdout)
    if not cleaned:
        raise RuntimeError("llama-cli returned an empty response")
    return cleaned


def optimize(source: str, template_name: str = "auto") -> str:
    source = source.strip()
    if not source:
        raise RuntimeError("Input prompt is empty")
    status = ensure_local_model()
    prompt = build_inference_prompt(source, template_name)
    if status["backend"] == "ollama":
        return _optimize_with_ollama(status["ollamaCommand"], status["ollamaModel"], prompt)
    if status["backend"] == "llama.cpp":
        return _optimize_with_llama_cpp(status["llamaCli"], model_path(), prompt)
    raise RuntimeError("Local model setup did not produce a usable backend")


def _read_source(args: argparse.Namespace) -> str:
    return sys.stdin.read() if args.stdin else args.input


def main() -> int:
    parser = argparse.ArgumentParser(description="Prompt Optimizer Mini local model manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Report local model status")
    subparsers.add_parser("ensure", help="Install or reuse a local model")
    optimize_parser = subparsers.add_parser("optimize", help="Optimize a prompt with the local model")
    optimize_parser.add_argument("--stdin", action="store_true")
    optimize_parser.add_argument("--input", default="")
    optimize_parser.add_argument("--template", default="auto")
    render_parser = subparsers.add_parser("render-prompt", help="Render the few-shot request without inference")
    render_parser.add_argument("--stdin", action="store_true")
    render_parser.add_argument("--input", default="")
    render_parser.add_argument("--template", default="auto")
    args = parser.parse_args()

    try:
        if args.command == "status":
            print(json.dumps(get_status(), ensure_ascii=False))
        elif args.command == "ensure":
            print(json.dumps(ensure_local_model(), ensure_ascii=False))
        elif args.command == "render-prompt":
            print(build_inference_prompt(_read_source(args), args.template))
        else:
            print(optimize(_read_source(args), args.template))
    except Exception as exc:  # Keep CLI errors concise for the extension UI.
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
