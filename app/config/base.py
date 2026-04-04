from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).resolve().parent.parent.parent


PROJECT_ROOT = get_project_root()
CONFIG_DIR = PROJECT_ROOT / "config"


