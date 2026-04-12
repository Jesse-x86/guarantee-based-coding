from pathlib import Path

from app.config.backups import META_BACKUPS
from app.core import executor
from app.models.errors import GuaranteeDuplicatedError, GuaranteeNotFoundError, \
    GuaranteeTestFailedError
from app.models.meta import FileMeta, Guarantee
from app.utils.json_model_operator import save_model_to_json

def register(meta: FileMeta, target: str, guarantee: Guarantee):
    """
    注册新的保证
    :param meta:
    :param target:
    :param guarantee:
    :return:
    """
    existing_items = meta.guarantees.get(target, [])
    for item in existing_items:
        if guarantee.guarantee_path == item.guarantee_path:
            raise GuaranteeDuplicatedError(guarantee_path=item.guarantee_path, target_file=target)

    result = executor.verify_single(meta.config, file=guarantee.guarantee_path, return_model=True)
    if not result.return_code == 0:
        raise GuaranteeTestFailedError(target_file=target, guarantee_path=guarantee.guarantee_path,
                                       failure_info=result.stderr)

    existing_items.append(guarantee)
    meta.guarantees[target] = existing_items


def unregister(meta: FileMeta, target: str, guarantee_path: str):
    """
    取消注册单个保证
    :param meta:
    :param target:
    :param guarantee_path:
    :return:
    """
    existing_items = meta.guarantees.get(target, [])
    for index, item in enumerate(existing_items):
        if guarantee_path == item.guarantee_path:
            existing_items.pop(index)
            meta.guarantees[target] = existing_items
            return
    raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee_path)


def unregister_all(meta: FileMeta, target: str):
    """
    取消注册单个文件的所有保证
    :param meta:
    :param target:
    :return:
    """
    if target not in meta.guarantees:
        raise GuaranteeNotFoundError(guarantee_path="Any", target_file=target)

    del meta.guarantees[target]


def list_all(meta: FileMeta) -> dict[str, list[Guarantee]]:
    return meta.guarantees.copy()


def list_all_for_one(meta: FileMeta, target: str) -> list[Guarantee]:
    existing_items = meta.guarantees.get(target, [])
    return existing_items.copy()


def update(meta: FileMeta, target: str, guarantee: Guarantee):
    existing_items = meta.guarantees.get(target, [])
    index = -1
    for _index, _item in enumerate(existing_items):
        if guarantee.guarantee_path == _item.guarantee_path:
            index = _index
            break
    if index < 0:
        raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee.guarantee_path)

    result = executor.verify_single(meta.config, file=guarantee.guarantee_path, return_model=True)
    if not result.return_code == 0:
        raise GuaranteeTestFailedError(target_file=target, guarantee_path=guarantee.guarantee_path, failure_info=result.stderr)

    existing_items[index].guarantee_desc = guarantee.guarantee_desc
    existing_items[index].timeout_override = guarantee.timeout_override


def verify_all(meta: FileMeta, *, timeout: int = -1, single_output: bool = False, return_model: bool = True):
    result_dict = {}

    if single_output:
        return_model = False

    for target, existing_items in meta.guarantees.items():
        result_list = []
        for item in existing_items:
            # 优先使用传入的运行时 timeout，若为 -1 则尝试使用模型自带的 override
            current_timeout = timeout if timeout != -1 else item.timeout_override
            result_list.append(executor.verify_single(meta.config, file=item.guarantee_path,
                                                      timeout=current_timeout, return_model=return_model))
        if single_output:
            result_dict[target] = all(result_list)
        else:
            result_dict[target] = result_list

    return result_dict


def verify_all_of_one_target(meta: FileMeta, target: str, *, timeout: int = -1, single_output: bool = False, return_model: bool = True):
    existing_items = meta.guarantees.get(target, [])
    result_list = []

    if single_output:
        return_model = False

    for item in existing_items:
        current_timeout = timeout if timeout != -1 else item.timeout_override
        result_list.append(executor.verify_single(meta.config, file=item.guarantee_path, timeout=current_timeout, return_model=return_model))

    if single_output:
        return all(result_list)

    return result_list


def verify_single(meta: FileMeta, target: str, guarantee_path: str, *, timeout: int = -1, return_model: bool = True):
    existing_items = meta.guarantees.get(target, [])
    for item in existing_items:
        if guarantee_path == item.guarantee_path:
            current_timeout = timeout if timeout != -1 else item.timeout_override
            return executor.verify_single(meta.config, file=item.guarantee_path, timeout=current_timeout, return_model=return_model)
    raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee_path)