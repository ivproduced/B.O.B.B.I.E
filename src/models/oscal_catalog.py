from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class Prop:
    name: str
    value: str
    ns: str | None = None
    clazz: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "Prop":
        return cls(
            name=str(payload.get("name", "")),
            value=str(payload.get("value", "")),
            ns=payload.get("ns"),
            clazz=payload.get("class"),
        )


@dataclass
class Link:
    href: str
    rel: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "Link":
        return cls(href=str(payload.get("href", "")), rel=payload.get("rel"))


@dataclass
class Select:
    how_many: str | None = None
    choice: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "Select":
        return cls(
            how_many=payload.get("how-many"),
            choice=[str(item) for item in payload.get("choice", [])],
        )


@dataclass
class Parameter:
    id: str
    props: list[Prop] = field(default_factory=list)
    label: str | None = None
    values: list[str] = field(default_factory=list)
    select: Select | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "Parameter":
        return cls(
            id=str(payload.get("id", "unknown-param-id")),
            props=[Prop.from_dict(item) for item in payload.get("props", [])],
            label=payload.get("label"),
            values=[str(item) for item in payload.get("values", [])],
            select=Select.from_dict(payload["select"]) if payload.get("select") else None,
        )


@dataclass
class Part:
    id: str | None
    name: str
    title: str | None = None
    prose: str | None = None
    subparts: list["Part"] = field(default_factory=list)
    props: list[Prop] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "Part":
        return cls(
            id=payload.get("id"),
            name=str(payload.get("name", "unknown-part-name")),
            title=payload.get("title"),
            prose=payload.get("prose"),
            subparts=[Part.from_dict(item) for item in payload.get("parts", [])],
            props=[Prop.from_dict(item) for item in payload.get("props", [])],
        )


@dataclass
class Control:
    id: str
    title: str
    control_class: str
    props: list[Prop] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    params: list[Parameter] = field(default_factory=list)
    parts: list[Part] = field(default_factory=list)
    enhancements: list["Control"] = field(default_factory=list)
    baselines: dict[str, bool] = field(
        default_factory=lambda: {
            "LOW": False,
            "MODERATE": False,
            "HIGH": False,
            "PRIVACY": False,
        }
    )
    in_custom_baseline: bool = False

    @classmethod
    def from_dict(cls, payload: dict) -> "Control":
        return cls(
            id=str(payload.get("id", "")).lower(),
            title=str(payload.get("title", "Untitled Control")),
            control_class=str(payload.get("class", "")),
            props=[Prop.from_dict(item) for item in payload.get("props", [])],
            links=[Link.from_dict(item) for item in payload.get("links", [])],
            params=[Parameter.from_dict(item) for item in payload.get("params", [])],
            parts=[Part.from_dict(item) for item in payload.get("parts", [])],
            enhancements=[Control.from_dict(item) for item in payload.get("controls", [])],
        )

    @property
    def assessment_objectives(self) -> list[Part]:
        for part in self.parts:
            if part.name.lower() == "assessment-objective":
                return part.subparts
        return []

    @property
    def flat_assessment_objectives(self) -> list[Part]:
        objectives: list[Part] = []

        def walk(node: Part, depth: int = 0) -> None:
            if depth > 15:
                return
            if node.name.lower() == "assessment-objective" and node.id and (node.prose or "").strip():
                objectives.append(node)
                return
            for child in node.subparts:
                walk(child, depth + 1)

        for part in self.parts:
            walk(part, 0)

        deduped: dict[str, Part] = {item.id: item for item in objectives if item.id}
        return list(deduped.values())


@dataclass
class Group:
    id: str
    title: str
    controls: list[Control] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "Group":
        return cls(
            id=str(payload.get("id", "unknown-group-id")),
            title=str(payload.get("title", "Unknown Group Title")),
            controls=[Control.from_dict(item) for item in payload.get("controls", [])],
        )


@dataclass
class Catalog:
    controls: list[Control] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "Catalog":
        catalog = payload.get("catalog", {})
        groups = [Group.from_dict(item) for item in catalog.get("groups", [])]

        unique: dict[str, Control] = {}

        def add_control(control: Control) -> None:
            if control.id not in unique:
                unique[control.id] = control
            for enhancement in control.enhancements:
                add_control(enhancement)

        for group in groups:
            for control in group.controls:
                add_control(control)

        for control_payload in catalog.get("controls", []):
            add_control(Control.from_dict(control_payload))

        sorted_controls = sorted(unique.values(), key=lambda item: item.id)
        return cls(controls=sorted_controls, groups=groups)


def load_catalog(path: str) -> Catalog:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Catalog.from_dict(payload)
