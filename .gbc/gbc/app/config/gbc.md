# 意图
回答四个问题：在哪个项目上工作、用户级偏好存在哪里、meta 写入保留几份备份、怎么跑测试。当前项目根在进程启动时按固定优先级 GBC_PROJECT_ROOT > cwd 确定，不向上猜；set_current_project() 供 CLI --project/-C、MCP/editor 与测试显式覆盖。用户级偏好独立于目标项目，绝不落进项目 .gbc。其余（备份份数、executor 配置）仍是进程内单例 + 环境变量驱动。

# 文件

## base.py
PROJECT_ROOT / CONFIG_DIR(基于本包文件位置推算)。其他 config 模块的锚点。

## project.py
当前目标项目根的运行时状态：进程启动时按 GBC_PROJECT_ROOT > cwd 确定一次默认根，不向上搜索；set_current_project(path) 显式覆盖且优先，供叶子命令 --project/-C、mcp/editor 与测试使用。一切 .gbc 路径都相对该固定根。

## backups.py
META_BACKUPS:由环境变量 GBC_META_BACKUPS 决定,meta 落盘时保留几份备份。

## executor.py
ExecutorModel(command/cwd/timeout/env_ops) / ExecutorsConfig + executors.json 落盘(在目标项目 .gbc/ 下)。语言无关:把"怎么跑某类测试"配成具名 executor,保证只引用名字。依赖 utils.json_model_operator 读写、core.env 用其 EnvAction。
