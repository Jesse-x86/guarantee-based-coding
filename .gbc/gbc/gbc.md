# 意图
GBC 可分发 Python 包，pip 安装后提供 gbc。entry.py 是纯分发器，组合保证引擎、架构意图 intent、离线手册 doc 和服务入口。随包手册来自 docs/ 单一内容源，安装后独立于源码仓库；项目状态仍由目标项目 .gbc/ 持有。

# 文件

## entry.py
gbc 单一入口，组合保证/tree/intent/doc 与 MCP/editor/rules/setup/lang。intent 管项目架构意图，doc 查离线手册；不保留旧意图 doc 别名；局部语言仅显式给出时覆盖根语言。

## app/
GBC 工具本体源代码根，经 [project.scripts] 暴露 gbc 命令。保证引擎（interface/core/models/config/utils）与项目架构意图（intent）分别维护可验证行为和职责约束；documentation 提供随版本分发的只读手册查询，i18n 为横切支撑。项目可变状态保存在目标项目 .gbc/，手册查询不依赖项目。
