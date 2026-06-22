"""gbc MCP server 启动器。

为什么需要它:本工具跑在 Windows conda python,而调用方(Claude Code)在 WSL。实测
WSL→Windows 进程**环境变量传不进去**(GBC_PROJECT_PATH/PYTHONUTF8 都会丢),且目标项目可能
有同名 `app/` 包会按 cwd 抢占 import。所以这里全部用进程内 / argv 解决,不依赖 env 或 cwd:

用法:  python <serve.py 的绝对路径> [目标项目根的绝对路径]
"""
import sys
from pathlib import Path

# 1) 本仓上 sys.path。按绝对路径调用脚本时其目录本就在 sys.path[0](不是 cwd),
#    所以 import 到的永远是本工具的 app,不会被目标项目的同名 app 抢占;这里再保险一次。
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 2) JSON-RPC 走 stdout —— 强制 UTF-8,避免 Windows 本地码页(gbk)污染协议流。
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 3) 目标项目根由 argv 传入(环境变量在 WSL→Windows 下不可靠)。
from app.config import project
if len(sys.argv) > 1:
    project.set_current_project(sys.argv[1])

# 4) 起 stdio server。
from app.interface.mcp import mcp
mcp.run()
