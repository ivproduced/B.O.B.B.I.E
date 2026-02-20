from __future__ import annotations

from dataclasses import dataclass, field
import re


def control_id_sort_key(control_id: str) -> tuple:
    pattern = re.compile(r"([a-zA-Z]+)-(\d+)(?:\.([\w\d-]+))?(?:\((\w+)\))?(?:_([a-zA-Z]+))?(?:\.([\w\d-]+))?")
    match = pattern.match(control_id.lower())
    if not match:
        return (control_id.lower(), 0, "", 0, "", "")

    prefix = match.group(1) or ""
    main_number = int(match.group(2) or 0)
    part_id = match.group(3) or match.group(6) or ""
    enhancement = int(match.group(4) or 0)
    objective_suffix = match.group(5) or ""
    return (prefix, main_number, part_id, enhancement, objective_suffix, control_id.lower())


@dataclass
class LlmPlaceholderDefinition:
    id: str
    label: str
    description: str
    examples: list[str] = field(default_factory=list)
    frequency_group_key: str | None = None
    document_group_key: str | None = None
    role_group_key: str | None = None
    semantic_group: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "LlmPlaceholderDefinition":
        label = str(payload.get("label", "Unknown Label"))
        description = str(payload.get("description", "No description."))
        ll = label.lower()
        dl = description.lower()

        frequency_group_key = None
        if any(token in ll or token in dl for token in ["frequency", "interval", "periodic"]):
            if "frequency" in ll or "frequency" in dl:
                frequency_group_key = "frequency"
            elif "interval" in ll or "interval" in dl:
                frequency_group_key = "interval"
            else:
                frequency_group_key = "periodicity"

        document_group_key = "document" if any(token in ll or token in dl for token in ["document", "doc"]) else None
        role_group_key = "role" if any(token in ll or token in dl for token in ["role", "responsible", "assigned"]) else None

        examples = payload.get("llm_examples") or payload.get("examples") or []
        return cls(
            id=str(payload.get("id", "unknown_id")),
            label=label,
            description=description,
            examples=[str(item) for item in examples],
            frequency_group_key=frequency_group_key,
            document_group_key=document_group_key,
            role_group_key=role_group_key,
            semantic_group=payload.get("semantic_group"),
        )


@dataclass
class LlmObjectiveStatement:
    objective_id: str
    objective_prose_original: str
    llm_generated_statement: str
    llm_generated_question: str
    placeholders: list[LlmPlaceholderDefinition] = field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "LlmObjectiveStatement":
        placeholder_items = payload.get("placeholders_in_statement")
        if placeholder_items is None:
            placeholder_items = payload.get("placeholders_in_summary", [])
        placeholders = [
            LlmPlaceholderDefinition.from_dict(item)
            for item in placeholder_items
            if isinstance(item, dict)
        ]
        return cls(
            objective_id=str(payload.get("objective_key", "unknown_objective_key")),
            objective_prose_original=str(payload.get("objective_prose_original", "Prose not available.")),
            llm_generated_statement=str(payload.get("llm_generated_implementation_statement", "Statement not available.")),
            llm_generated_question=str(payload.get("llm_generated_question", "Question not available.")),
            placeholders=placeholders,
            error=payload.get("error"),
        )


@dataclass
class LlmControlObjectiveData:
    control_id: str
    control_title: str
    llm_generated_objective_statements: list[LlmObjectiveStatement] = field(default_factory=list)
    placeholders: list[LlmPlaceholderDefinition] = field(default_factory=list)
    llm_generated_control_summary: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "LlmControlObjectiveData":
        key = "assessment_objectives" if isinstance(payload.get("assessment_objectives"), list) else "objectives"
        objective_statements = [
            LlmObjectiveStatement.from_dict(item)
            for item in payload.get(key, [])
            if isinstance(item, dict)
        ]
        objective_statements.sort(key=lambda item: control_id_sort_key(item.objective_id))

        flattened: dict[str, LlmPlaceholderDefinition] = {}
        for statement in objective_statements:
            for placeholder in statement.placeholders:
                flattened.setdefault(placeholder.id, placeholder)

        return cls(
            control_id=str(payload.get("control_id", "unknown_id")),
            control_title=str(payload.get("control_title", "Untitled")),
            llm_generated_objective_statements=objective_statements,
            placeholders=list(flattened.values()),
            llm_generated_control_summary=payload.get("llm_generated_control_summary"),
        )

    def get_placeholders_for_objective(self, objective_id: str) -> list[LlmPlaceholderDefinition]:
        prefix = f"{objective_id}_ph_"
        return [placeholder for placeholder in self.placeholders if placeholder.id.startswith(prefix)]
