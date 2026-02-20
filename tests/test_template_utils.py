from src.models.information_system import ControlImplementation
from src.models.llm_objective_data import LlmControlObjectiveData
from src.models.baseline_profile import BaselineProfile
from src.utils.ssp_statement_template_utils import get_final_statement_for_control, replace_placeholders_plain_text


def test_replace_placeholders_plain_text_marks_missing() -> None:
    template = "Assigned role is [AssignedRole] and tool is [Tool]."
    result = replace_placeholders_plain_text(template, {"AssignedRole": "ISSO"})
    assert "ISSO" in result
    assert "[Tool] (Needs Input)" in result


def test_get_final_statement_for_control_renders_objective_text() -> None:
    impl = ControlImplementation(
        status="Implemented",
        implementation_details="Control implementation narrative.",
        llm_objective_placeholder_values={
            "ac-2_obj.a-1": {"[AssignedRole]": "ISSO"}
        },
    )

    llm_data = LlmControlObjectiveData.from_dict(
        {
            "control_id": "ac-2",
            "control_title": "Account Management",
            "assessment_objectives": [
                {
                    "objective_key": "ac-2_obj.a-1",
                    "objective_prose_original": "Original prose",
                    "llm_generated_implementation_statement": "Assigned role is [AssignedRole].",
                    "llm_generated_question": "Who is assigned?",
                    "placeholders_in_statement": [
                        {"id": "ac-2_obj.a-1_ph_1", "label": "AssignedRole", "description": "Role"}
                    ],
                }
            ],
        }
    )

    result = get_final_statement_for_control("ac-2", impl, llm_data)
    assert "Assigned role is ISSO." in result


def test_baseline_profile_from_dict_supports_camel_case_key() -> None:
    profile = BaselineProfile.from_dict(
        {
            "id": "custom-1",
            "title": "Custom Baseline",
            "selectedControlIds": ["AC-2", "PM-9"],
        }
    )
    assert profile.selected_control_ids == ["ac-2", "pm-9"]


def test_llm_objective_placeholder_fallback_key_is_supported() -> None:
    llm_data = LlmControlObjectiveData.from_dict(
        {
            "control_id": "ac-2",
            "control_title": "Account Management",
            "assessment_objectives": [
                {
                    "objective_key": "ac-2_obj.a-1",
                    "objective_prose_original": "Original prose",
                    "llm_generated_implementation_statement": "Assigned role is [AssignedRole].",
                    "llm_generated_question": "Who is assigned?",
                    "placeholders_in_summary": [
                        {"id": "ac-2_obj.a-1_ph_1", "label": "AssignedRole", "description": "Role"}
                    ],
                }
            ],
        }
    )

    assert len(llm_data.placeholders) == 1
