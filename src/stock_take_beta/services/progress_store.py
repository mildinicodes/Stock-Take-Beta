import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import PROGRESS_FILE


DEFAULT_STATE: dict[str, Any] = {
    "version": 2,
    "marketplace_items": [],
    "marketplace_counts": {},
    "missing_sku": [],
    "duplicates": [],
    "audit": {},
    "unlisted_physical_stock": [],
    "last_refreshed_at": None,
    "audit_completed_at": None,
    "completion_summary": None,
    "updated_at": None,
}


class ProgressStore:
    """Local JSON store shared by desktop and mobile audit views."""

    def __init__(self, path: Path = PROGRESS_FILE) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return deepcopy(DEFAULT_STATE)
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                saved = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return deepcopy(DEFAULT_STATE)
        state = deepcopy(DEFAULT_STATE)
        state.update(saved if isinstance(saved, dict) else {})
        return state

    def save(self, state: dict[str, Any]) -> None:
        state = dict(state)
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        temp_path = self.path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        temp_path.replace(self.path)
