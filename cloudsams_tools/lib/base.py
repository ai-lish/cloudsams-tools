"""
cloudsams_tools.lib.base — opt-in helpers for tool authors（ARCHITECTURE.md §3.1）。

呢啲 helper 淨係消除樣板，**唔係強制**。一個 tool 唔 import 呢個檔都完全合法 ——
contract 係 `main.py::run(argv) -> int`，唔係「必須用 base」。

stdlib only：呢個檔屬於 `cloudsams_tools` core，唔可以拉第三方 dep
（見 ARCHITECTURE.md §3.2 / §1.3.3 —— 唔可以整爛零-dep 嘅 `cloudsams list`）。
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path


def add_common_io_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """統一 `--input` / `--output-dir` 嘅 flag 名、type=Path、help 文字。"""
    parser.add_argument("--input", required=True, type=Path, help="Source file")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output folder")
    return parser


def resolve_output_dir(path: Path) -> Path:
    """mkdir(parents=True, exist_ok=True) 之後回傳同一個 Path，方便 chain。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logger(tool_name: str):
    """
    回傳一個好簡單嘅 log function：`log(msg)` 印去 stderr，帶 `[tool_name]` prefix。
    Emoji prefix（✂️ / ✅ 之類）由 tool 自己喺 msg 入面加，base 唔規定。
    """
    def log(msg: str) -> None:
        print(f"[{tool_name}] {msg}", file=sys.stderr)
    return log


def die(msg: str, code: int = 1) -> "NoReturn":  # type: ignore[name-defined]
    """統一錯誤退出：印 `❌ <msg>` 落 stderr，然後 sys.exit(code)。"""
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


@dataclass
class Tool:
    """
    可選嘅結構化基底。想要嘅 tool 可以喺 `run()` 入面自己組一個 `Tool` instance
    嚟攞 `self.log`；唔想用（大部分細 tool）就直接寫 function-style `run(argv)`，
    完全唔使掂呢個 class。
    """
    name: str
    args: argparse.Namespace = field(default_factory=argparse.Namespace)

    def __post_init__(self) -> None:
        self.log = get_logger(self.name)
