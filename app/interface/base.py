import pathlib
from pathlib import Path

from app.config.project import CURRENT_PROJECT
from app.core.guarantee import initialize
from app.models.errors import IllegalFilePathError


def init(file: str, lang: str) -> None:
    file = Path(file)
    if file.is_relative_to(CURRENT_PROJECT):
        return initialize(file, lang)

    raise IllegalFilePathError(file)