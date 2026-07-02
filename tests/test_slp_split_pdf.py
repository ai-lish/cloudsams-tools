"""Smoke test for slp-split-pdf: create a synthetic 5-page PDF, split, verify."""
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# Allow `import split` from sibling folder
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "slp-split-pdf"))
import split  # noqa: E402


def make_dummy_pdf(path: Path, n_pages: int = 5) -> None:
    """Write a minimal PDF with n blank pages."""
    writer = PdfWriter()
    for _ in range(n_pages):
        writer.add_blank_page(width=595, height=842)  # A4
    with open(path, "wb") as f:
        writer.write(f)


def test_per_page_split(tmp_path: Path) -> None:
    src = tmp_path / "slp-sample.pdf"
    out = tmp_path / "out"
    make_dummy_pdf(src, n_pages=5)

    rc = split.split_pdf(src, out, mode="per-page", pages=None)
    assert rc == 0

    files = sorted(out.glob("*.pdf"))
    assert len(files) == 5, f"expected 5 files, got {len(files)}"
    for f in files:
        assert f.name.startswith("slp-sample_page-")
        assert PdfReader(str(f)).pages.__len__() == 1


def test_range_split(tmp_path: Path) -> None:
    src = tmp_path / "slp-sample.pdf"
    out = tmp_path / "out"
    make_dummy_pdf(src, n_pages=10)

    rc = split.split_pdf(src, out, mode="range", pages="1-3,7,9-10")
    assert rc == 0

    files = sorted(out.glob("*.pdf"))
    assert len(files) == 3
    assert (out / "slp-sample_pages-001-003.pdf").exists()
    assert (out / "slp-sample_pages-007-007.pdf").exists()
    assert (out / "slp-sample_pages-009-010.pdf").exists()
    # total pages across outputs should equal 3 + 1 + 2 = 6
    total = sum(len(PdfReader(str(f)).pages) for f in files)
    assert total == 6


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
