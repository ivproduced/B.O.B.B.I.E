from __future__ import annotations

from pathlib import Path

import pytest

from scripts.extract_architecture_diagram import extract_mermaid_diagram, main


def test_extract_mermaid_diagram_returns_block_content() -> None:
    markdown = """
# Demo

```mermaid
flowchart TD
    A --> B
```
"""
    diagram = extract_mermaid_diagram(markdown)
    assert diagram == "flowchart TD\n    A --> B\n"


def test_extract_mermaid_diagram_raises_without_block() -> None:
    with pytest.raises(ValueError, match="No mermaid diagram block"):
        extract_mermaid_diagram("# No diagram here")


def test_main_writes_extracted_diagram(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "README.md"
    output = tmp_path / "arch" / "architecture.mmd"
    source.write_text("```mermaid\nflowchart TD\nA --> B\n```\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "extract_architecture_diagram.py",
            "--source",
            str(source),
            "--output",
            str(output),
        ],
    )

    exit_code = main()
    assert exit_code == 0
    assert output.read_text(encoding="utf-8") == "flowchart TD\nA --> B\n"
