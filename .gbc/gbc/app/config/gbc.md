# 意图
回答三个问题:在哪个项目上工作、meta 写入保留几份备份、怎么跑测试。多为进程内单例 + 环境变量驱动。

# 文件

## base.py
PROJECT_ROOT / CONFIG_DIR(基于本包文件位置推算)。其他 config 模块的锚点。

## project.py
当前目标项目根:由环境变量 GBC_PROJECT_PATH 决定,set_current_project 可运行时改、get_current_project 读取。一切 .gbc 路径都相对它。

## backups.py
META_BACKUPS:由环境变量 GBC_META_BACKUPS 决定,meta 落盘时保留几份备份。

## executor.py
ExecutorModel(command/cwd/timeout/env_ops) / ExecutorsConfig + executors.json 落盘(在目标项目 .gbc/ 下)。语言无关:把"怎么跑某类测试"配成具名 executor,保证只引用名字。依赖 utils.json_model_operator 读写、core.env 用其 EnvAction。
