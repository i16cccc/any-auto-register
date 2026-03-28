from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


_DATA_FILE = Path(__file__).resolve().parent.parent / "resources" / "provider_driver_templates.json"


def _load_templates() -> dict[str, list[dict]]:
    with _DATA_FILE.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {
        str(provider_type): list(items or [])
        for provider_type, items in dict(raw or {}).items()
    }


def _clone(items: list[dict]) -> list[dict]:
    return deepcopy(items)


def list_driver_templates(provider_type: str) -> list[dict]:
    templates = _load_templates()
    return _clone(templates.get(provider_type, []))


def list_builtin_provider_definitions(provider_type: str) -> list[dict]:
    return list_driver_templates(provider_type)


def get_driver_template(provider_type: str, driver_type: str) -> dict | None:
    for item in list_driver_templates(provider_type):
        if item.get("driver_type") == driver_type:
            return item
    return None
