from pathlib import Path

from app.config.backups import META_BACKUPS
from app.models.meta import FileMeta
from app.utils.json_model_operator import save_model_to_json


def initialize(file: Path, lang: str) -> None:
    model = FileMeta(lang=lang, guarantees={})
    try:
        save_model_to_json(model, file, META_BACKUPS)
    except Exception as e:
        raise