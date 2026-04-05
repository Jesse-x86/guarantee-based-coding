from pathlib import Path
from typing import Optional

from app.config.project import CURRENT_PROJECT
from app.core.guarantee import initialize, register, unregister, list_all, update, unregister_all
from app.models.errors import IllegalFilePathError
from app.models.meta import Guarantee

def _normalize_provider(provider: str) -> Path:
    provider = Path(provider)
    if not provider.is_relative_to(CURRENT_PROJECT):
        raise IllegalFilePathError(provider)
    return provider

def initialize_guarantee(provider: str, config: str) -> None:
    provider = _normalize_provider(provider)
    return initialize(provider, config)

def register_guarantee(provider: str, target: str, path: str, spec: str) -> None:
    provider = _normalize_provider(provider)
    guarantee = Guarantee(guarantee_path=path, guarantee_desc=spec)
    return register(provider, target, guarantee)

def unregister_guarantee(provider: str, target: str, path: str) -> None:
    provider = _normalize_provider(provider)
    return unregister(provider, target, guarantee_path=path)

def unregister_all_guarantees(provider: str, target: str) -> None:
    provider = _normalize_provider(provider)
    return unregister_all(provider, target)

def list_guarantees(provider: str, target: str) -> str:
    provider = _normalize_provider(provider)
    return list_all(provider, target)

def update_guarantees(provider: str, target: str, path: str, spec: str) -> None:
    provider_path = _normalize_provider(provider)
    guarantee = Guarantee(guarantee_path=path, guarantee_desc=spec)
    return update(provider_path, target, guarantee)

def upsert_executor():
    ...

def verify_all():
    ...

def verify_single_guarantee():
    ...