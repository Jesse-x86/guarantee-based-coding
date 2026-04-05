from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from app.config.executor import Executor
from app.config.project import CURRENT_PROJECT
from app.core import executor
from app.core.guarantee import initialize, register, unregister, list_all, update, erase_guarantee, verify_single, \
    verify_all
from app.models.errors import IllegalFilePathError, ExecutorConfigInvalidError
from app.models.meta import Guarantee
from app.models.verify import VerifyModel


def _normalize_provider(provider: str) -> Path:
    provider_path = Path(provider).resolve()
    if not provider_path.is_relative_to(CURRENT_PROJECT):
        raise IllegalFilePathError(provider_path)
    return provider_path

# ======== Guarantees ========

def initialize_guarantee(provider: str, config: str) -> None:
    provider_path = _normalize_provider(provider)
    return initialize(provider_path, config)

def register_guarantee(provider: str, target: str, path: str, spec: str) -> None:
    provider_path = _normalize_provider(provider)
    guarantee = Guarantee(guarantee_path=path, guarantee_desc=spec)
    return register(provider_path, target, guarantee)

def unregister_guarantee(provider: str, target: str, path: str) -> None:
    provider_path = _normalize_provider(provider)
    return unregister(provider_path, target, guarantee_path=path)

def erase_all_guarantees(provider: str, target: str) -> None:
    provider_path = _normalize_provider(provider)
    return erase_guarantee(provider_path, target)

def list_guarantees(provider: str, target: str) -> str:
    provider_path = _normalize_provider(provider)
    return list_all(provider_path, target)

def update_guarantees(provider: str, target: str, path: str, spec: str) -> None:
    provider_path = _normalize_provider(provider)
    guarantee = Guarantee(guarantee_path=path, guarantee_desc=spec)
    return update(provider_path, target, guarantee)

# ======== Verify ========

def verify_all_guarantees(provider: str, target: str, *, timeout: int = -1, single_output: bool = False, return_model: bool = True) -> bool | list[bool] | list[VerifyModel]:
    provider_path = _normalize_provider(provider)
    return verify_all(provider=provider_path, target=target, timeout=timeout, single_output=single_output, return_model=return_model)

def verify_single_guarantee(provider: str, target: str, path: str, *, timeout: int = -1, return_model: bool = True) -> bool | VerifyModel:
    provider_path = _normalize_provider(provider)
    return verify_single(provider=provider_path, target=target, guarantee_path=path, timeout=timeout, return_model=return_model)

# ======== Executors ========

def upsert_executor(config_name: str, config_data: dict):
    try:
        model = Executor(**config_data)
        executor.upsert_executor(config_name=config_name, model=model)
    except ValidationError as e:
        raise ExecutorConfigInvalidError(config_name)