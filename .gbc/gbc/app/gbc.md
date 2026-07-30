# 意图
GBC 工具本体的源代码根（充当 src 的源代码仓库），经 [project.scripts] 暴露 gbc 命令。下分保证引擎（interface + core + models + config + utils）与意图文档（intent）两个对称子系统，i18n 为横切支撑。工具仓自身只读无状态，一切可变状态落在目标项目的 .gbc/ 下。

# 文件

## i18n/
GBC 面向用户输出的多语言资源与语言判定。当前支持简体中文(zh)与英文(en)，默认回退 en(发布英文优先)。语言判定优先级：显式 --lang > 环境变量 GBC_LANG > 系统 locale > en。
两类文本分治：**短消息**(错误信息、命令成功提示、help)走查表式 catalog(键→多语言串)；**长文本**(gbc rules 规则集、gbc setup 接线指南)按语言存独立 Markdown 资源文件、按当前语言整篇读出。资源随包分发。

## interface/
把引擎能力暴露成「人/agent 能用的形态」，并把「外部形态」与「内部实现」彻底解耦：cli、mcp、web 编辑器都只是薄表面，真正的编排、路径解析、文件读写收在 base 一处。换表面不动引擎。
命令收口为单一入口 gbc(pyproject [project.scripts])：单次执行的子命令(guarantee/dep/verify/doctor/executor/refactor/tree/doc/setup/rules) + 两个常驻服务(gbc mcp up / gbc editor up)。所有面向用户的文本一律经 i18n 层产出，不硬编码。

## intent/
意图文档(gbc.md)子系统。与保证引擎(core + interface)对称：base 是唯一 IO/编排点(路径解析、gbc.md 读写、父子意图单源投影、整树读写、全树一致性)；cli(gbc doc)、mcp(经 interface.mcp 暴露的 doc 工具)与 editor(web)都是薄表面，只调 base、不碰磁盘。意图读(show/check)与写(set-*/sync/migrate)都可经 MCP，写入的人类确认闸门由用户 agent 框架承担。gbc.md 解析单源复用 utils.gbc_md。

## assets.py
静态资源定位的单一入口：把随包分发的数据(i18n catalog/texts、editor 前端、给 CLI-only agent 的预组 skills)集中到 gbc/assets/ 下并暴露路径常量(I18N_CATALOG_DIR/I18N_TEXTS_DIR/EDITOR_FRONTEND_DIR/SKILLS_DIR)。代码与数据分离；加一类资源只需在此登记一处 + 打包声明一条。

## config/
回答三个问题:在哪个项目上工作、meta 写入保留几份备份、怎么跑测试。当前项目根默认是进程启动时的 cwd,可运行时用 set_current_project 显式覆盖(常驻服务如 mcp up/editor up 靠这个接收显式参数);其余(备份份数、executor 配置)仍是进程内单例 + 环境变量驱动。

## models/
所有层共享的 pydantic 模型。模型即契约:无业务逻辑、无 IO。改一个字段就是改契约,下游(core / interface / 落盘的 .gbc json)全靠它,要慎重。

## core/
保证系统的核心逻辑与"怎么真的把测试跑起来"。纯模型操作:不解析路径、不读写 .gbc 文件(那是 base 的活)。进出本层的文件路径一律是项目相对字符串。

## utils/
无业务语义的通用工具:.gbc 路径映射、json↔模型、原子写文件。被各层使用,不依赖业务层。
