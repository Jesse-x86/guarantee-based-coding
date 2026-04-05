from pathlib import Path

from app.config.backups import META_BACKUPS
from app.config.project import CURRENT_PROJECT
from app.models.errors import GuaranteeDuplicatedError, MetaNotFoundError, GuaranteeNotFoundError
from app.models.meta import FileMeta, Guarantee
from app.utils.json_model_operator import save_model_to_json, load_model_from_json


def _to_json_path(provider: Path):
    relative_path = provider.relative_to(CURRENT_PROJECT)
    target_dir = CURRENT_PROJECT / ".gbc" / relative_path.parent
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
        if not json_model:
            raise MetaNotFoundError(original_file=provider, target_file=target)

        existing_items = json_model.guarantees.get(target, [])
        for item in existing_items:
            if guarantee.guarantee_path == item.guarantee_path:
                raise GuaranteeDuplicatedError(guarantee_path=item.guarantee_path, target_file=target)

        # TODO: 测试，失败则返回

        existing_items.append(guarantee)

        json_model.guarantees[target] = existing_items

        save_model_to_json(json_model, json_path, META_BACKUPS)
    except Exception as e:
        raise

def unregister_all(provider: Path, target: str):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)
        if not json_model:
            raise MetaNotFoundError(original_file=provider, target_file=target)

        json_model.guarantees[target] = []
        save_model_to_json(json_model, json_path, META_BACKUPS)
        return
    except Exception as e:
        raise


def unregister(provider: Path, target: str, guarantee_path: str):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)
        if not json_model:
            raise MetaNotFoundError(original_file=provider, target_file=target)

        if not guarantee_path:
            json_model.guarantees[target] = []
            save_model_to_json(json_model, json_path, META_BACKUPS)
            return

        existing_items = json_model.guarantees.get(target, [])
        for index, item in enumerate(existing_items):
            if guarantee_path == item.guarantee_path:
                existing_items.pop(index)
                json_model.guarantees[target] = existing_items
                save_model_to_json(json_model, json_path, META_BACKUPS)
                return
        raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee_path)
    except Exception as e:
        raise


def list_all(provider: Path, target: str):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)
        if not json_model:
            raise MetaNotFoundError(original_file=provider, target_file=target)

        existing_items = json_model.guarantees.get(target, [])

        return ",\n".join([item.model_dump_json() for item in existing_items])
    except Exception as e:
        raise


def update(provider: Path, target: str, guarantee: Guarantee):
    try:
        json_path = _to_json_path(provider)

        json_model = load_model_from_json(json_path, FileMeta)
        if not json_model:
            raise MetaNotFoundError(original_file=provider, target_file=target)

        existing_items = json_model.guarantees.get(target, [])
        item = None
        for _item in existing_items:
            if guarantee.guarantee_path == _item.guarantee_path:
                item = _item
        if not item:
            raise GuaranteeNotFoundError(target_file=target, guarantee_path=guarantee.guarantee_path)

        # TODO: 测试，失败则返回

        item.guarantee_desc = guarantee.guarantee_desc

        save_model_to_json(json_model, json_path, META_BACKUPS)
    except Exception as e:
        raise