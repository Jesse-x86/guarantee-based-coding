from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from app.config.backups import META_BACKUPS
from app.config.executor import ExecutorModel
from app.config.project import get_current_project
from app.core import executor
from app.core.guarantee import register, unregister, list_all_for_one, update, unregister_all, \
    verify_single, \
    verify_all_of_one_target, verify_all, list_all
from app.models.errors import IllegalFilePathError, ExecutorConfigInvalidError, MetaNotFoundError
from app.models.meta import Guarantee, FileMeta
from app.models.verify import VerifyModel
from app.utils.file_utils import to_gbc_json_path
from app.utils.json_model_operator import load_model_from_json, save_model_to_json

@contextmanager
def meta_session(provider_str: str, readonly: bool = False, create_if_missing: bool = False):
    """
    统一处理 Provider 路径校验、模型加载、异常转换及自动保存
    :param provider_str: 输入的原始 provider 文件字符串
    :param readonly: 如果为 True，退出时不会保存文件
    :param create_if_missing: 如果文件不存在，是否创建一个新的 FileMeta 对象
    """
    provider_path = Path(provider_str).resolve()
    if not provider_path.is_relative_to(get_current_project()):
        raise IllegalFilePathError(provider_path)

    json_path = to_gbc_json_path(provider_path)

    try:
        if json_path.exists():
            json_model = load_model_from_json(json_path, FileMeta)
        elif create_if_missing:
            json_model = FileMeta(guarantees={})
        else:
            raise MetaNotFoundError(original_file=provider_path, target_file=json_path)

        yield json_model

        # 只有在非只读模式且模型存在时才保存
        if not readonly and json_model is not None:
            save_model_to_json(json_model, json_path, META_BACKUPS)

    except Exception:
        raise

# ======== Guarantees 写操作 ========

def register_guarantee(
    provider: str,
    config: str,
    target: str,
    guarantee_path: str,
    guarantee_spec: str,
    timeout_override: int = -1
) -> None:
    guarantee = Guarantee(
        config=config,
        guarantee_path=guarantee_path,
        guarantee_desc=guarantee_spec,
        timeout_override=timeout_override  # 存入模型
    )
    # 注册新测试时允许文件不存在
    with meta_session(provider, readonly=False, create_if_missing=True) as meta:
        return register(meta, target, guarantee)

def unregister_guarantee(
    provider: str,
    target: str,
    guarantee_path: str
) -> None:
    with meta_session(provider, readonly=False) as meta:
        return unregister(meta, target, guarantee_path=guarantee_path)

def unregister_all_guarantees(
    provider: str,
    target: str
) -> None:
    with meta_session(provider, readonly=False) as meta:
        return unregister_all(meta, target)

def update_guarantees(
    provider: str,
    target: str,
    guarantee_path: str,
    guarantee_spec: str,
    timeout_override: int = -1
) -> None:
    # 更新模型数据
    guarantee = Guarantee(
        guarantee_path=guarantee_path,
        guarantee_desc=guarantee_spec,
        timeout_override=timeout_override # 存入模型
    )
    with meta_session(provider, readonly=False) as meta:
        return update(meta, target, guarantee)

# ======== Guarantees 读操作 ========

def list_guarantees_of_one(provider: str, target: str) -> list[Guarantee]:
    with meta_session(provider, readonly=True) as meta:
        return list_all_for_one(meta, target)

def list_guarantees_of_all(provider: str) -> dict[str, list[Guarantee]]:
    with meta_session(provider, readonly=True) as meta:
        return list_all(meta)

# ======== Verify 操作 ========

def verify_all_guarantees(
    provider: str,
    *,
    timeout: int = -1,
    single_output: bool = False,
    return_model: bool = True
) -> dict:
    with meta_session(provider, readonly=True) as meta:
        return verify_all(meta, timeout=timeout, single_output=single_output, return_model=return_model)

def verify_all_guarantees_of_one_target(
    provider: str,
    target: str,
    *,
    timeout: int = -1,
    single_output: bool = False,
    return_model: bool = True
) -> list:
    with meta_session(provider, readonly=True) as meta:
        return verify_all_of_one_target(meta, target=target, timeout=timeout, single_output=single_output, return_model=return_model)

def verify_single_guarantee(
    provider: str,
    target: str,
    guarantee_path: str,
    *,
    timeout: int = -1,
    return_model: bool = True
) -> VerifyModel:
    with meta_session(provider, readonly=True) as meta:
        return verify_single(meta, target=target, guarantee_path=guarantee_path, timeout=timeout, return_model=return_model)

# ======== Executors ========

def upsert_executor(config_name: str, config_data: dict):
    try:
        model = ExecutorModel(**config_data)
        executor.upsert_exec_config(config_name=config_name, model=model)
    except ValidationError as e:
        raise ExecutorConfigInvalidError(config_name)