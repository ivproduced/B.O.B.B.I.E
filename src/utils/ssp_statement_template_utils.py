from __future__ import annotations

import re

from src.models.information_system import ControlImplementation
from src.models.llm_objective_data import LlmControlObjectiveData


def replace_placeholders_plain_text(template: str, values: dict[str, str]) -> str:
    if not template:
        return ""

    placeholder_re = re.compile(r"\[([^\]]+)\]")

    def _repl(match: re.Match[str]) -> str:
        key = match.group(1)
        value = values.get(key, "").strip()
        if value:
            return value
        return f"{match.group(0)} (Needs Input)"

    return placeholder_re.sub(_repl, template)


def fill_llm_template(template: str, filled_values: dict[str, str]) -> str:
    return replace_placeholders_plain_text(template, filled_values)


def get_final_statement_for_control(
    control_id: str,
    control_implementation: ControlImplementation | None,
    llm_control_data: LlmControlObjectiveData | None,
) -> str:
    if control_implementation is None:
        return f"Control implementation details not available for {control_id}."

    lines: list[str] = []
    lines.append(f"### {control_id.upper()} Implementation Statement")

    if control_implementation.implementation_details.strip():
        lines.append(control_implementation.implementation_details.strip())
    else:
        lines.append(f"*The overall implementation details for {control_id.upper()} have not yet been defined.*")

    lines.append("")

    if llm_control_data and llm_control_data.llm_generated_objective_statements:
        lines.append("#### Objective-Specific Details:")
        for statement in llm_control_data.llm_generated_objective_statements:
            raw_values = control_implementation.llm_objective_placeholder_values.get(statement.objective_id, {})
            transformed = {k.replace("[", "").replace("]", ""): v for k, v in raw_values.items()}
            rendered = replace_placeholders_plain_text(statement.llm_generated_statement, transformed)
            lines.append(f"**{statement.objective_id.upper()}:**")
            lines.append(rendered)
            lines.append("")
    else:
        lines.append("_(No specific LLM-enhanced objective statements were processed for this control.)_")
        lines.append("")

    if control_implementation.notes.strip():
        lines.append("#### Additional Control Notes:")
        lines.append(control_implementation.notes.strip())

    return "\n".join(lines).strip()
