from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BaselineProfile:
    id: str
    title: str
    selected_control_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "selected_control_ids": self.selected_control_ids,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "BaselineProfile":
        selected_ids = payload.get("selected_control_ids")
        if selected_ids is None:
            selected_ids = payload.get("selectedControlIds")
        return cls(
            id=str(payload.get("id", "")),
            title=str(payload.get("title", "")),
            selected_control_ids=[str(value).lower() for value in (selected_ids or [])],
        )
