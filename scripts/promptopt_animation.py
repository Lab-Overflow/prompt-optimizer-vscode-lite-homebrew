#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time
from typing import Optional, TextIO


FINAL_ART = r"""
  .----------------------------------------------------------------.
  |  ____                           _    ___        _              |
  | |  _ \ _ __ ___  _ __ ___  _ __ | |_ / _ \ _ __ | |_           |
  | | |_) | '__/ _ \| '_ ` _ \| '_ \| __| | | | '_ \| __|          |
  | |  __/| | | (_) | | | | | | |_) | |_| |_| | |_) | |_           |
  | |_|   |_|  \___/|_| |_| |_| .__/ \__|\___/| .__/ \__|          |
  |                           |_|             |_|                  |
  |----------------------------------------------------------------|
  | [OK] ignition     [OK] route matrix  [OK] prompt forge         |
  |                                                                |
  |   >>>>>>>>>>>>>>>>>>> PROMPTOPT ONLINE <<<<<<<<<<<<<<<<<<       |
  |          homebrew-native / lightweight / ready                  |
  '----------------------------------------------------------------'
"""

PALETTE = {
    "dim": "\033[2m",
    "scan": "\033[97m",
    "cyan": "\033[96m",
    "ready": "\033[92m",
    "reset": "\033[0m",
}


def _lines() -> list[str]:
    return FINAL_ART.strip("\n").splitlines()


def _width(lines: list[str]) -> int:
    return max(len(line) for line in lines)


def _supports_color() -> bool:
    return not os.environ.get("NO_COLOR")


def _color(text: str, name: str) -> str:
    if not _supports_color() or not text:
        return text
    return f"{PALETTE[name]}{text}{PALETTE['reset']}"


def reveal_frame(progress: int, *, scan_width: int = 3, ready: bool = False) -> str:
    lines = _lines()
    width = _width(lines)
    visible_until = max(0, min(progress, width))
    rendered: list[str] = []

    for line in lines:
        padded = line.ljust(width)
        shown = padded[:visible_until]
        beam = padded[visible_until : min(visible_until + scan_width, width)]
        hidden = " " * max(width - visible_until - len(beam), 0)
        if ready:
            rendered.append(_color(shown.rstrip(), "ready"))
            continue
        rendered.append(
            _color(shown, "cyan")
            + _color(beam, "scan")
            + _color(hidden, "dim")
        )
    return "\n".join(rendered)


def show_banner(enabled: bool = True, stream: Optional[TextIO] = None) -> None:
    if not enabled:
        return
    stream = stream or sys.stderr
    if not stream.isatty():
        print("PromptOpt :: homebrew-native prompt forge online", file=stream)
        return

    clear = "\033[2J\033[H"
    width = _width(_lines())
    for progress in range(0, width + 4, 4):
        print(clear, end="", file=stream)
        print(reveal_frame(progress), file=stream)
        time.sleep(0.035)

    print(clear, end="", file=stream)
    print(reveal_frame(width, ready=True), file=stream)


if __name__ == "__main__":
    show_banner()
