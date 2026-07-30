# 意图
回答三个问题:在哪个项目上工作、meta 写入保留几份备份、怎么跑测试。当前项目根默认是进程启动时的 cwd,可运行时用 set_current_project 显式覆盖(常驻服务如 mcp up/editor up 靠这个接收显式参数);其余(备份份数、executor 配置)仍是进程内单例 + 环境变量驱动。

# 文件

## base.py
PROJECT_ROOT / CONFIG_DIR(基于本包文件位置推算)。其他 config 模块的锚点。

## project.py
当前目标项目根的运行时状态：get_current_project() 黔回进程启动时的 cwd（CLI 单次命令「当前项目 = 跑命令时所在目录」，无环境变量、不回退包安装位置）；set_current_project() 供常驻服务（mcp up / editor up）显式覆盖。一切 .gbc 路径都相对它。

## backups.py
META_BACKUPS:由环境变量 GBC_META_BACKUPS 决定,meta 落盘时保留几份备份。

## executor.py
ExecutorModel(command/cwd/timeout/env_ops) / ExecutorsConfig + executors.json 落盘(在目标项目 .gbc/ 下)。语言无关:把"怎么跑某类测试"配成具名 executor,保证只引用名字。依赖 utils.json_model_operator 读写、core.env 用其 EnvAction。
