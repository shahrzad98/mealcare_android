from __future__ import annotations

import json
import os
from collections.abc import Callable
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from threading import RLock

from app_data import make_default_data


def get_data_directory() -> Path:
    try:
        from android.storage import app_storage_path

        path = Path(app_storage_path())
    except (ImportError, RuntimeError):
        custom_path = os.environ.get("MEALCARE_DATA_DIR")
        path = Path(custom_path) if custom_path else Path.home() / ".mealcare"

    path.mkdir(parents=True, exist_ok=True)
    return path


def _merge_defaults(current: object, default: object) -> object:
    if isinstance(default, dict):
        current_dict = current if isinstance(current, dict) else {}
        result: dict[str, object] = {}
        for key, value in default.items():
            result[key] = _merge_defaults(current_dict.get(key), value)
        for key, value in current_dict.items():
            if key not in result:
                result[key] = deepcopy(value)
        return result

    if isinstance(default, list):
        return deepcopy(current) if isinstance(current, list) else deepcopy(default)

    return deepcopy(default) if current is None else deepcopy(current)


class DataStore:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or get_data_directory()
        self.path = self.directory / "mealcare_data.json"
        self._lock = RLock()

    def load(self) -> dict[str, object]:
        with self._lock:
            if not self.path.exists():
                data = make_default_data()
                self.save(data)
                return data

            try:
                parsed = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                parsed = {}

            merged = _merge_defaults(parsed, make_default_data())
            if not isinstance(merged, dict):
                merged = make_default_data()
            return merged

    def save(self, data: dict[str, object]) -> None:
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            temporary_path = self.path.with_suffix(".tmp")
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)

    def update(self, mutator: Callable[[dict[str, object]], None]) -> dict[str, object]:
        with self._lock:
            data = self.load()
            mutator(data)
            self.save(data)
            return data

    def reset(self) -> dict[str, object]:
        data = make_default_data()
        self.save(data)
        return data


class NotificationState:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or get_data_directory()
        self.path = self.directory / "notification_state.json"
        self._lock = RLock()

    def mark_if_new(self, key: str) -> bool:
        with self._lock:
            state = self._load()
            sent = state.get("sent", {})
            if not isinstance(sent, dict):
                sent = {}

            if key in sent:
                return False

            sent[key] = date.today().isoformat()
            cutoff = date.today() - timedelta(days=3)
            cleaned = {
                item_key: item_date
                for item_key, item_date in sent.items()
                if isinstance(item_date, str) and item_date >= cutoff.isoformat()
            }
            self._save({"sent": cleaned})
            return True

    def _load(self) -> dict[str, object]:
        if not self.path.exists():
            return {"sent": {}}
        try:
            parsed = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"sent": {}}
        return parsed if isinstance(parsed, dict) else {"sent": {}}

    def _save(self, state: dict[str, object]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temporary_path.replace(self.path)
