# 意图
GBC 工具本体的可分发 Python 包(pip install 后经 [project.scripts] 暴露 gbc 命令)。entry.py 是唯一入口纯分发器，把 app/ 下两个子系统(保证引擎 interface + 意图文档 intent)的表面组合成命令树。工具仓自身只读无状态，一切可变状态落在目标项目的 .gbc/ 下。

# 文件

## entry.py
唯一入口 gbc 命令的纯分发器：组合 interface.cli(保证命令) + intent.cli(doc) + mcp up + editor up + rules/setup。不实现业务，只做命令树组合。[project.scripts] 的 gbc 指向本模块 app。

## app/
GBC 工具本体的源代码根（充当 src 的源代码仓库），经 [project.scripts] 暴露 gbc 命令。下分保证引擎（interface + core + models + config + utils）与意图文档（intent）两个对称子系统，i18n 为横切支撑。工具仓自身只读无状态，一切可变状态落在目标项目的 .gbc/ 下。
