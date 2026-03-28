"""平台插件注册表 - 自动扫描 platforms/ 目录加载插件"""
import importlib
import json
import pkgutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Type
from sqlmodel import Session, select
from .base_platform import BasePlatform
from .db import PlatformCapabilityOverrideModel, engine

_registry: Dict[str, Type[BasePlatform]] = {}
_PLATFORM_CAPABILITIES_FILE = Path(__file__).resolve().parent.parent / "resources" / "platform_capabilities.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def register(cls: Type[BasePlatform]):
    """装饰器：注册平台插件"""
    _registry[cls.name] = cls
    return cls


def load_all():
    """自动扫描并加载 platforms/ 下所有插件"""
    import platforms
    for finder, name, _ in pkgutil.iter_modules(platforms.__path__, platforms.__name__ + "."):
        try:
            importlib.import_module(f"{name}.plugin")
        except ModuleNotFoundError:
            pass


def get(name: str) -> Type[BasePlatform]:
    if name not in _registry:
        raise KeyError(f"平台 '{name}' 未注册，已注册: {list(_registry.keys())}")
    return _registry[name]


def _load_platform_capability_bootstrap() -> dict[str, dict]:
    with _PLATFORM_CAPABILITIES_FILE.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {
        str(name): dict(payload or {})
        for name, payload in dict(raw or {}).items()
    }


def _bootstrap_platform_capabilities(cls: Type[BasePlatform]) -> dict[str, list[str]]:
    bootstrap = _load_platform_capability_bootstrap().get(cls.name) or {}
    return {
        "supported_executors": list(bootstrap.get("supported_executors", [])),
        "supported_identity_modes": list(bootstrap.get("supported_identity_modes", [])),
        "supported_oauth_providers": list(bootstrap.get("supported_oauth_providers", [])),
    }


def _normalize_platform_capabilities(data: dict | None, cls: Type[BasePlatform]) -> dict[str, list[str]]:
    bootstrap = _bootstrap_platform_capabilities(cls)
    payload = data if isinstance(data, dict) else {}
    normalized: dict[str, list[str]] = {}
    for key, fallback in bootstrap.items():
        raw = payload.get(key)
        if isinstance(raw, list):
            normalized[key] = [str(item) for item in raw if str(item or "").strip()]
        else:
            normalized[key] = list(fallback)
    return normalized


def _ensure_platform_capabilities_seeded(session: Session) -> dict[str, PlatformCapabilityOverrideModel]:
    items = session.exec(select(PlatformCapabilityOverrideModel)).all()
    by_name = {item.platform_name: item for item in items}
    changed = False
    for cls in _registry.values():
        if cls.name in by_name:
            continue
        item = PlatformCapabilityOverrideModel(platform_name=cls.name)
        item.created_at = _utcnow()
        item.updated_at = _utcnow()
        item.set_capabilities(_bootstrap_platform_capabilities(cls))
        session.add(item)
        by_name[cls.name] = item
        changed = True
    if changed:
        session.commit()
        items = session.exec(select(PlatformCapabilityOverrideModel)).all()
        by_name = {item.platform_name: item for item in items}
    return by_name


def get_platform_capabilities(name: str) -> dict[str, list[str]]:
    cls = get(name)
    with Session(engine) as session:
        by_name = _ensure_platform_capabilities_seeded(session)
        item = by_name.get(name)
        if item:
            return _normalize_platform_capabilities(item.get_capabilities(), cls)
    return _bootstrap_platform_capabilities(cls)


def list_platforms() -> list:
    with Session(engine) as session:
        persisted = _ensure_platform_capabilities_seeded(session)
        result = []
        for cls in _registry.values():
            item = persisted.get(cls.name)
            caps = _normalize_platform_capabilities(item.get_capabilities() if item else None, cls)
            result.append({
                "name": cls.name,
                "display_name": cls.display_name,
                "version": cls.version,
                **caps,
            })
        return result
