from __future__ import annotations

from src.agents.base_family_agent import BaseFamilyAgent
from src.agents.families.ac import ACFamilyAgent
from src.agents.families.au import AUFamilyAgent
from src.agents.families.cm import CMFamilyAgent
from src.agents.families.ia import IAFamilyAgent
from src.agents.families.pl import PLFamilyAgent
from src.agents.families.pm import PMFamilyAgent
from src.agents.families.ra import RAFamilyAgent
from src.agents.families.si import SIFamilyAgent


class StubFamilyAgent(BaseFamilyAgent):
    def __init__(self, family_id: str, controls_supported: list[str] | None = None):
        self.family_id = family_id
        self.controls_supported = controls_supported or []


FAMILY_IDS = [
    "AC", "AT", "AU", "CA", "CM", "CP", "IA", "IR", "MA", "MP",
    "PE", "PL", "PM", "PS", "PT", "RA", "SA", "SC", "SI", "SR",
]

FAMILY_REGISTRY: dict[str, BaseFamilyAgent] = {
    family_id: StubFamilyAgent(family_id=family_id) for family_id in FAMILY_IDS
}

FAMILY_REGISTRY["PL"] = PLFamilyAgent()
FAMILY_REGISTRY["PM"] = PMFamilyAgent()
FAMILY_REGISTRY["AC"] = ACFamilyAgent()
FAMILY_REGISTRY["AU"] = AUFamilyAgent()
FAMILY_REGISTRY["CM"] = CMFamilyAgent()
FAMILY_REGISTRY["IA"] = IAFamilyAgent()
FAMILY_REGISTRY["RA"] = RAFamilyAgent()
FAMILY_REGISTRY["SI"] = SIFamilyAgent()


def get_family_agent(family_id: str) -> BaseFamilyAgent:
    agent = FAMILY_REGISTRY.get(family_id)
    if agent is None:
        raise KeyError(
            f"Family '{family_id}' is not registered in FAMILY_REGISTRY. "
            f"Valid family IDs are: {sorted(FAMILY_REGISTRY.keys())}"
        )
    return agent

# Populate known controls_supported for demo families (helps plan validation)
FAMILY_REGISTRY["PL"].controls_supported = ["PL-2"]
FAMILY_REGISTRY["PM"].controls_supported = ["PM-9"]
FAMILY_REGISTRY["AC"].controls_supported = ["AC-2", "AC-7"]
FAMILY_REGISTRY["AU"].controls_supported = ["AU-3"]
FAMILY_REGISTRY["CM"].controls_supported = ["CM-8"]
FAMILY_REGISTRY["IA"].controls_supported = ["IA-5"]
FAMILY_REGISTRY["RA"].controls_supported = ["RA-5"]
FAMILY_REGISTRY["SI"].controls_supported = ["SI-2", "SI-4"]


def validate_plan_vs_registry(control_plan: dict[str, list[str]]) -> None:
    """Validate that every control in the plan maps to a single registered family and,
    if known, that the family agent declares support for the control. Raises ValueError on mismatch.
    """
    errors: list[str] = []
    for fam, ctrls in control_plan.items():
        if fam not in FAMILY_REGISTRY:
            errors.append(f"Unknown family in plan: {fam}")
            continue
        agent = FAMILY_REGISTRY[fam]
        for c in ctrls:
            # Prefix check
            if not str(c).upper().startswith(fam + "-"):
                errors.append(f"Control {c} does not match family prefix {fam}")
            # If agent declares supported controls, ensure control listed
            supported = getattr(agent, "controls_supported", None)
            if supported and str(c) not in supported:
                errors.append(f"Family {fam} does not declare support for control {c}")

    if errors:
        raise ValueError("Plan vs registry validation failed: " + "; ".join(errors))
