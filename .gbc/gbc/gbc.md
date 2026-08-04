# 意图
GBC 工具本体的可分发 Python 包(pip install 后经 [project.scripts] 暴露 gbc 命令)。entry.py 是唯一入口纯分发器，把 app/ 下两个子系统(保证引擎 interface + 意图文档 intent)的表面组合成命令树。工具仓自身只读无状态，一切可变状态落在目标项目的 .gbc/ 下。

# 文件

## entry.py
唯一入口 gbc 的纯分发器：组合保证命令、doc、mcp/editor、rules/setup 与用户语言偏好命令 gbc lang [zh|en|auto]。lang 无参数显示当前有效/持久状态；setup/rules/editor 的局部 --lang 仅明确传值时覆盖根 callback，避免空值把已选语言重置。

## app/
GBC 工具本体的源代码根（充当 src 的源代码仓库），经 [project.scripts] 暴露 gbc 命令。下分保证引擎（interface + core + models + config + utils）与意图文档（intent）两个对称子系统，i18n 为横切支撑。工具仓自身只读无状态，一切可变状态落在目标项目的 .gbc/ 下。
