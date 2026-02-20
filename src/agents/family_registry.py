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
    return FAMILY_REGISTRY[family_id]
