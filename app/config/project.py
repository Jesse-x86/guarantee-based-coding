import os
from pathlib import Path

from app.config.base import PROJECT_ROOT

# 初始化当前路径
def _init_current_project() -> Path:
    var = os.environ.get("GBC_PROJECT_PATH", None)
    if var:
        var = Path(var)
        if var.exists():
            return var

    return PROJECT_ROOT / "workspace"

# 会被使用的当前路径变量
CURRENT_PROJECT = _init_current_project()

# 更新当前路径
def set_current_project(new_path: str):
    new_path = Path(new_path)

    global CURRENT_PROJECT
    CURRENT_PROJECT = new_path