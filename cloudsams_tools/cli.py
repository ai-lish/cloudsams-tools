"""
cloudsams — 頂層 dispatcher。

用法：
  cloudsams list                        # 列出所有 tool（唔 import 任何 tool）
  cloudsams <tool> [tool args...]       # 只 import <tool>，其餘 argv 原封傳落去
  cloudsams --help

兩層 dispatch（見 ARCHITECTURE.md §1.4）：頂層只認 `list` 同 tool 名，
其餘 argv 完全交畀選中 tool 自己嘅 argparse。冇中央 subparser tree，
所以加 tool 唔使改呢個檔，亦唔會啟動時 import 晒所有 tool。
"""
from __future__ import annotations

import importlib.util
import sys
from types import ModuleType

from .discovery import ToolInfo, find_tool, iter_tools


def _print_list() -> int:
    """`cloudsams list` —— discovery demo（全 repo 唯一有真邏輯嘅命令之一）。"""
    tools = list(iter_tools())
    if not tools:
        print("（未有 tool。cp -r tools/_template tools/<name> 開始。）")
        return 0

    name_w = max(len(t.name) for t in tools)
    status_w = max(len(t.status) for t in tools)
    runtime_w = max(len(t.runtime) for t in tools)
    header = f"{'NAME':<{name_w}}  {'STATUS':<{status_w}}  {'RUNTIME':<{runtime_w}}  SUMMARY"
    print(header)
    for t in tools:
        print(f"{t.name:<{name_w}}  {t.status:<{status_w}}  {t.runtime:<{runtime_w}}  {t.summary}")
    return 0


def _import_tool_main(info: ToolInfo) -> ModuleType:
    """
    Lazy import 選中 tool 嘅 entry module（e.g. tools/<name>/main.py）。

    用 importlib spec 由檔案直接載入，並把 tool folder 加入 sys.path，
    等 tool 內部可以 `import split` / `import parsing` 咁 import 自己嘅 sibling module。
    只喺呢一刻先觸發 tool 嘅第三方 dep —— 故障隔離嘅關鍵。
    """
    tool_dir = str(info.path)
    if tool_dir not in sys.path:
        sys.path.insert(0, tool_dir)  # 令 tool 內部 sibling import work

    spec = importlib.util.spec_from_file_location(
        f"cloudsams_tool_{info.name.replace('-', '_')}", info.entry_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"無法載入 entry: {info.entry_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # 此刻先執行 tool 嘅 import（可能缺 dep → 拋錯，只影響呢個 tool）
    return module


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        print("\nAvailable tools:\n")
        return _print_list()

    cmd, rest = argv[0], argv[1:]

    if cmd == "list":
        return _print_list()

    info = find_tool(cmd)
    if info is None:
        print(f"❌ 未知 tool: {cmd!r}。試下 `cloudsams list`。", file=sys.stderr)
        return 2

    if info.runtime != "python":
        # runtime: node 等日後先接（見 ARCHITECTURE.md §9 未做項）。
        print(f"❌ runtime {info.runtime!r} 暫未支援 dispatch。", file=sys.stderr)
        return 2

    try:
        module = _import_tool_main(info)
    except Exception as exc:  # noqa: BLE001 — 一個壞 tool 唔應拖冧 CLI，只報佢
        print(f"❌ 載入 tool {cmd!r} 失敗：{exc}", file=sys.stderr)
        print("   （可能未 pip install -r 佢嘅 requirements.txt？）", file=sys.stderr)
        return 1

    if not hasattr(module, "run"):
        print(f"❌ tool {cmd!r} 冇 `run(argv)` entrypoint。", file=sys.stderr)
        return 1

    return int(module.run(rest) or 0)


if __name__ == "__main__":
    sys.exit(main())
