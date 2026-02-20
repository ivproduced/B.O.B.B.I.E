from pathlib import Path

from src.parsers.baseline_loader import load_standard_baselines
from src.parsers.oscal_loader import load_catalog_and_tag_baselines


def test_load_standard_baselines_and_tagging() -> None:
    root = Path(__file__).resolve().parent.parent
    baselines = load_standard_baselines(str(root))

    assert "LOW" in baselines
    assert len(baselines["LOW"].selected_control_ids) > 0

    catalog = load_catalog_and_tag_baselines(
        catalog_path=str(root / "NIST_SP-800-53_rev5_catalog.json"),
        baselines=baselines,
    )

    groups = catalog["catalog"]["groups"]
    first_control = groups[0]["controls"][0]
    assert "baselines" in first_control
    assert set(first_control["baselines"].keys()) == {"LOW", "MODERATE", "HIGH", "PRIVACY"}
