from __future__ import annotations

import json
from pathlib import Path

from src.models.baseline_profile import BaselineProfile


class BaselineManager:
    def __init__(self, storage_path: str = "data/mock/user_baselines.json"):
        self.storage_path = Path(storage_path)
        self.user_baselines: list[BaselineProfile] = []

    def load_user_baselines(self) -> list[BaselineProfile]:
        if not self.storage_path.exists():
            self.user_baselines = []
            return self.user_baselines

        raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        self.user_baselines = [BaselineProfile.from_dict(item) for item in raw]
        return self.user_baselines

    def save_user_baseline(self, profile: BaselineProfile) -> None:
        self.load_user_baselines()
        index = next((i for i, value in enumerate(self.user_baselines) if value.id == profile.id), None)
        if index is None:
            self.user_baselines.append(profile)
        else:
            self.user_baselines[index] = profile
        self._persist()

    def delete_user_baseline(self, baseline_id: str) -> None:
        self.load_user_baselines()
        self.user_baselines = [profile for profile in self.user_baselines if profile.id != baseline_id]
        self._persist()

    def _persist(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [profile.to_dict() for profile in self.user_baselines]
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
