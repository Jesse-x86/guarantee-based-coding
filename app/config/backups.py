import os
from pathlib import Path

from app.config.base import PROJECT_ROOT

# 初始化备份数量
def _init_meta_backups() -> int:
    var = os.environ.get("GBC_META_BACKUPS", None)
    if var and var.isdigit():
        var = int(var)

    return 0

META_BACKUPS = _init_meta_backups()