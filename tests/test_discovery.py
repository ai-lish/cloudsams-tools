"""Tests for cloudsams_tools.discovery — mini-YAML parser + folder scan."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cloudsams_tools.discovery import find_tool, iter_tools, parse_mini_yaml  # noqa: E402


def test_parse_mini_yaml_handles_comments_blanks_and_quotes() -> None:
    text = """
    # this is a comment, should be skipped

    name: slp-split-pdf
    summary: 'Split things, quoted'
    status: "stable"
    # another comment
    runtime: python
    """
    meta = parse_mini_yaml(text)
    assert meta["name"] == "slp-split-pdf"
    assert meta["summary"] == "Split things, quoted"
    assert meta["status"] == "stable"
    assert meta["runtime"] == "python"


def test_parse_mini_yaml_ignores_lines_without_colon() -> None:
    text = "not-a-kv-line\nname: foo\n"
    meta = parse_mini_yaml(text)
    assert meta == {"name": "foo"}


def test_iter_tools_skips_template_and_dotfiles(tmp_path: Path) -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()

    # skipped: _template (leading underscore)
    (tools_dir / "_template").mkdir()
    (tools_dir / "_template" / "tool.yaml").write_text("name: _template\n")

    # skipped: .hidden (leading dot)
    (tools_dir / ".hidden").mkdir()
    (tools_dir / ".hidden" / "tool.yaml").write_text("name: hidden\n")

    # included: a real tool
    real = tools_dir / "real-tool"
    real.mkdir()
    (real / "tool.yaml").write_text("name: real-tool\nsummary: a real tool\nstatus: beta\n")

    names = [t.name for t in iter_tools(tools_dir)]
    assert names == ["real-tool"]


def test_iter_tools_skips_folder_without_manifest(tmp_path: Path) -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "no-manifest").mkdir()  # no tool.yaml inside

    assert list(iter_tools(tools_dir)) == []


def test_find_tool_locates_existing_slp_split_pdf() -> None:
    info = find_tool("slp-split-pdf")
    assert info is not None
    assert info.name == "slp-split-pdf"
    assert info.status == "stable"
    assert info.runtime == "python"
    assert info.entry_path.name == "main.py"
    assert info.entry_path.is_file()


def test_find_tool_returns_none_for_unknown_name() -> None:
    assert find_tool("does-not-exist") is None
