from __future__ import annotations

import argparse
from pathlib import Path


def extract_mermaid_diagram(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    inside_block = False
    block_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not inside_block and stripped == "```mermaid":
            inside_block = True
            continue

        if inside_block and stripped == "```":
            return "\n".join(block_lines).strip() + "\n"

        if inside_block:
            block_lines.append(line)

    raise ValueError("No mermaid diagram block was found in the provided markdown.")


def extract_from_file(source_path: Path) -> str:
    return extract_mermaid_diagram(source_path.read_text(encoding="utf-8"))


def write_diagram(diagram_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(diagram_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract the architecture mermaid diagram from README markdown.")
    parser.add_argument(
        "--source",
        default="README.md",
        help="Path to the markdown file containing the architecture mermaid block.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/architecture/architecture.mmd",
        help="Path where the extracted mermaid diagram should be written.",
    )
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    diagram = extract_from_file(source_path)
    write_diagram(diagram, output_path)
    print(f"Extracted architecture diagram to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
