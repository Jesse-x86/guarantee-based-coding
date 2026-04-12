from pathlib import Path

from app.config.project import get_current_project


def to_json_path(provider: Path):
    relative_path = provider.relative_to(get_current_project())
    target_dir = get_current_project() / ".gbc" / relative_path.parent
    target_filename = f"gbc.{relative_path.name}.json"
    json_path = target_dir / target_filename

    return json_path
