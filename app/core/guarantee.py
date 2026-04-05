from pathlib import Path

from pydantic import ValidationError

from app.config.backups import META_BACKUPS
from app.config.project import get_current_project
from app.core import executor
from app.models.errors import GuaranteeDuplicatedError, MetaNotFoundError, GuaranteeNotFoundError, \
    GuaranteeTestFailedError
from app.models.meta import FileMeta, Guarantee
from app.models.verify import VerifyModel
from app.utils.json_model_operator import save_model_to_json, load_model_from_json


def _to_json_path(provider: Path):
    relative_path = provider.relative_to(get_current_project())
    target_dir = get_current_project() / ".gbc" / relative_path.parent
    target_filename = f"gbc.{relative_path.name}.json"
    json_path = target_dir / target_filename

    return json_path

def initialize(provider: Path, config: str) -> None:
    model = FileMeta(config=config, guarantees={})
    try:
        json_path = _to_json_path(provider)

        save_model_to_json(model, json_path, META_BACKUPS)
    except Exception as e:
        raise

def register(provider: Path, target: str, guarantee: Guarantee):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        existing_items = json_model.guarantees.get(target, [])
        for item in existing_items:
            if guarantee.guarantee_path == item.guarantee_path:
                raise GuaranteeDuplicatedError(guarantee_path=item.guarantee_path, target_file=target)

        result = executor.verify_single(json_model.config, file=guarantee.guarantee_path, return_model=True)
        if not result.return_code == 0:
            raise GuaranteeTestFailedError(target_file=target, guarantee_path=guarantee.guarantee_path,
                                           failure_info=result.stderr)

        existing_items.append(guarantee)

        json_model.guarantees[target] = existing_items

        save_model_to_json(json_model, json_path, META_BACKUPS)
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise

def erase_guarantee(provider: Path, target: str):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)
        if target not in json_model.guarantees:
            raise GuaranteeNotFoundError(guarantee_path="Any", target_file=target)

        del json_model.guarantees[target]
        save_model_to_json(json_model, json_path, META_BACKUPS)
        return
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise


def unregister(provider: Path, target: str, guarantee_path: str):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        existing_items = json_model.guarantees.get(target, [])
        for index, item in enumerate(existing_items):
            if guarantee_path == item.guarantee_path:
                existing_items.pop(index)
                json_model.guarantees[target] = existing_items
                save_model_to_json(json_model, json_path, META_BACKUPS)
                return
        raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee_path)
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise

def list_all(provider: Path) -> dict[str, list[Guarantee]]:
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        return json_model.guarantees.copy()
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise

def list_all_for_one(provider: Path, target: str) -> list[Guarantee]:
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        existing_items = json_model.guarantees.get(target, [])

        return existing_items.copy()
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise


def update(provider: Path, target: str, guarantee: Guarantee):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        existing_items = json_model.guarantees.get(target, [])
        index = -1
        for _index, _item in enumerate(existing_items):
            if guarantee.guarantee_path == _item.guarantee_path:
                index = _index
                break
        if index < 0:
            raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee.guarantee_path)

        result = executor.verify_single(json_model.config, file=guarantee.guarantee_path, return_model=True)
        if not result.return_code == 0:
            raise GuaranteeTestFailedError(target_file=target, guarantee_path=guarantee.guarantee_path, failure_info=result.stderr)

        existing_items[index].guarantee_desc = guarantee.guarantee_desc

        save_model_to_json(json_model, json_path, META_BACKUPS)
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise

def verify_all(provider: Path, *, timeout: int = -1, single_output: bool = False, return_model: bool = True) -> dict[str, bool] | dict[str, list[bool]] | dict[str, list[VerifyModel]]:
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        result_dict = {}

        if single_output:
            return_model = False

        for target, existing_items in json_model.guarantees.items():
            result_list = []
            for index, item in enumerate(existing_items):
                result_list.append(executor.verify_single(json_model.config, file=item.guarantee_path,
                                                          timeout=timeout, return_model=return_model))
            if single_output:
                result_dict[target] = all(result_list)
            else:
                result_dict[target] = result_list

        return result_dict

    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise

def verify_all_of_one_target(provider: Path, target: str, *, timeout: int = -1, single_output: bool = False, return_model: bool = True) -> bool | list[bool] | list[VerifyModel]:
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        existing_items = json_model.guarantees.get(target, [])
        result_list = []

        if single_output:
            return_model = False

        for index, item in enumerate(existing_items):
            result_list.append(executor.verify_single(json_model.config, file=item.guarantee_path, timeout=timeout, return_model=return_model))

        if single_output:
            return all(result_list)

        return result_list

    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise


def verify_single(provider: Path, target: str, guarantee_path:str, *, timeout: int = -1, return_model: bool = True) -> bool | VerifyModel:
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)

        existing_items = json_model.guarantees.get(target, [])
        for index, item in enumerate(existing_items):
            if guarantee_path == item.guarantee_path:
                return executor.verify_single(json_model.config, file=item.guarantee_path, timeout=timeout, return_model=return_model)
        raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee_path)
    except FileNotFoundError as e:
        raise MetaNotFoundError(original_file=provider, target_file=json_path)
    except Exception as e:
        raise

