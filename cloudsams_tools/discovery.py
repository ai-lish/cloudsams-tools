"""
Tool discovery — 掃 tools/*/tool.yaml，回傳結構化 metadata。

設計重點（見 ARCHITECTURE.md §1.3 / §5）：
  - **唔 import 任何 tool**：淨係讀 tool.yaml 文字。所以就算某 tool 缺 dep 或
    main.py 有 syntax error，discovery / `cloudsams list` 同其他 tool 照行。
  - **零第三方依賴**：manifest 用內建 mini-YAML parser 讀，唔拉 PyYAML，
    令 `cloudsams list` 喺一個乜 dep 都未裝嘅乾淨 clone 都行到。

呢個檔同 cli.py 係全 repo 唯一有真邏輯嘅地方；其餘都係 skeleton。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# repo root = 呢個 package 嘅上一層；tools/ 喺 root 底下。
REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
MANIFEST_NAME = "tool.yaml"


@dataclass(frozen=True)
class ToolInfo:
    """一個 tool 嘅靜態 metadata（由 tool.yaml 嚟，冇 import 過 tool）。"""
    name: str
    summary: str
    status: str            # stable | beta | wip
    runtime: str           # python | node
    path: Path             # tools/<name>/
    entry: str             # 相對 path 嘅 entry file（預設 main.py）

    @property
    def entry_path(self) -> Path:
        return self.path / self.entry


def parse_mini_yaml(text: str) -> dict[str, str]:
    """
    極簡 flat `key: value` parser（**唔係**完整 YAML）。

    支援：`key: value`、`#` 註解、空行、value 兩邊嘅單／雙引號。
    刻意唔支援 nested / list —— manifest 一直保持 flat（見 ARCHITECTURE.md §5.2）。
    """
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()   # 去註解 + trim
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip("'\"")
        out[key.strip()] = value
    return out


def _load_one(tool_dir: Path) -> ToolInfo | None:
    """讀一個 folder 嘅 tool.yaml；唔合格（冇 manifest / 冇 name）就回 None。"""
    manifest = tool_dir / MANIFEST_NAME
    if not manifest.is_file():
        return None
    meta = parse_mini_yaml(manifest.read_text(encoding="utf-8"))
    name = meta.get("name")
    if not name:
        # 冇 name 嘅 manifest 當殘缺，skip（唔好拖冧 list）。
        return None
    return ToolInfo(
        name=name,
        summary=meta.get("summary", ""),
        status=meta.get("status", "wip"),
        runtime=meta.get("runtime", "python"),
        path=tool_dir,
        entry=meta.get("entry", "main.py"),
    )


def iter_tools(tools_dir: Path = TOOLS_DIR) -> Iterator[ToolInfo]:
    """Yield 所有合格 tool，按名排序。跳過 `_template` 同任何 `_`/`.` 開頭嘅 folder。"""
    if not tools_dir.is_dir():
        return
    for child in sorted(tools_dir.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        info = _load_one(child)
        if info is not None:
            yield info


def find_tool(name: str, tools_dir: Path = TOOLS_DIR) -> ToolInfo | None:
    """按 tool 名搵一個 tool（畀 dispatcher 用）。"""
    for info in iter_tools(tools_dir):
        if info.name == name:
            return info
    return None
