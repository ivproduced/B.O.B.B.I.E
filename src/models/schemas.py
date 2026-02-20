from pydantic import BaseModel, Field


class ControlAssessment(BaseModel):
    control_id: str = Field(description="NIST control ID")
    status: str = Field(description="PASS, FAIL, NOT_IMPLEMENTED, or ERROR")
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risk_level: str = Field(default="LOW")
    confidence_score: float = Field(default=0.0)
