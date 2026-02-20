from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssessmentObjectiveResponse:
    objective_key: str
    objective_prose: str
    is_met: bool
    user_notes: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "AssessmentObjectiveResponse":
        return cls(
            objective_key=str(payload.get("objectiveKey", payload.get("objective_key", ""))),
            objective_prose=str(payload.get("objectiveProse", payload.get("objective_prose", ""))),
            is_met=bool(payload.get("isMet", payload.get("is_met", False))),
            user_notes=payload.get("userNotes", payload.get("user_notes")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "objective_key": self.objective_key,
            "objective_prose": self.objective_prose,
            "is_met": self.is_met,
            "user_notes": self.user_notes,
        }


@dataclass
class ControlImplementation:
    status: str
    implementation_details: str = ""
    evidence: list[str] = field(default_factory=list)
    notes: str = ""
    llm_objective_placeholder_values: dict[str, dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "implementationDetails": self.implementation_details,
            "evidence": self.evidence,
            "notes": self.notes,
            "llmObjectivePlaceholderValues": self.llm_objective_placeholder_values,
        }


@dataclass
class InformationSystem:
    id: str
    name: str
    description: str = ""
    ato_status: str = "In Development"
    selected_baseline_id: str | None = None
    control_implementations: dict[str, ControlImplementation] = field(default_factory=dict)
    notes: str = ""
    assessment_objective_responses: dict[str, list[AssessmentObjectiveResponse]] = field(default_factory=dict)
    system_parameter_block_values: dict[str, str] = field(default_factory=dict)
    company_agency_name: str | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "InformationSystem":
        control_implementations = {
            str(k): control_implementation_from_dict(v)
            for k, v in dict(payload.get("controlImplementations", payload.get("control_implementations", {}))).items()
            if isinstance(v, dict)
        }

        objective_payload = payload.get("assessmentObjectiveResponses", payload.get("assessment_objective_responses", {}))
        assessment_objective_responses = {
            str(control_id): [
                AssessmentObjectiveResponse.from_dict(item)
                for item in values
                if isinstance(item, dict)
            ]
            for control_id, values in dict(objective_payload).items()
            if isinstance(values, list)
        }

        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            description=str(payload.get("description", "")),
            ato_status=str(payload.get("atoStatus", payload.get("ato_status", "In Development"))),
            selected_baseline_id=payload.get("selectedBaselineId", payload.get("selected_baseline_id")),
            control_implementations=control_implementations,
            notes=str(payload.get("notes", "")),
            assessment_objective_responses=assessment_objective_responses,
            system_parameter_block_values={
                str(k): str(v)
                for k, v in dict(payload.get("systemParameterBlockValues", payload.get("system_parameter_block_values", {}))).items()
            },
            company_agency_name=payload.get("companyAgencyName", payload.get("company_agency_name")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "ato_status": self.ato_status,
            "selected_baseline_id": self.selected_baseline_id,
            "control_implementations": {
                control_id: implementation.to_dict()
                for control_id, implementation in self.control_implementations.items()
            },
            "notes": self.notes,
            "assessment_objective_responses": {
                control_id: [response.to_dict() for response in responses]
                for control_id, responses in self.assessment_objective_responses.items()
            },
            "system_parameter_block_values": self.system_parameter_block_values,
            "company_agency_name": self.company_agency_name,
        }


def control_implementation_from_dict(payload: dict) -> ControlImplementation:
    return ControlImplementation(
        status=str(payload.get("status", "Not Implemented")),
        implementation_details=str(payload.get("implementationDetails", "")),
        evidence=[str(item) for item in payload.get("evidence", [])],
        notes=str(payload.get("notes", "")),
        llm_objective_placeholder_values={
            str(k): {str(kk): str(vv) for kk, vv in dict(v).items()}
            for k, v in dict(payload.get("llmObjectivePlaceholderValues", {})).items()
            if isinstance(v, dict)
        },
    )
