#!/usr/bin/env python3
"""
tools/_template/main.py — 新 tool 嘅起點。

Contract（ARCHITECTURE.md §2.1）：呢個檔只需要一個 `run(argv) -> int`。
Dispatcher（`cloudsams <name> ...`）會 import 呢個檔、叫 `run(rest_of_argv)`。
獨立行（`python main.py ...`）都應該一樣得。
"""
from __future__ import annotations

import argparse
import sys
from typing import List


def run(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="TODO: 講呢個 tool 做乜")
    # TODO: 加你自己嘅 args，例如：
    # p.add_argument("--input", required=True, type=Path)
    # p.add_argument("--output-dir", required=True, type=Path)
    p.parse_args(argv)

    print("edit me")  # TODO: 換成實際邏輯
    return 0


if __name__ == "__main__":
    sys.exit(run())
