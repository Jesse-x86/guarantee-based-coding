# 意图

# 文件

## i18n/
GBC 面向用户输出的多语言资源与语言判定。当前支持简体中文(zh)与英文(en)，默认回退 en(发布英文优先)。语言判定优先级：显式 --lang > 环境变量 GBC_LANG > 系统 locale > en。
两类文本分治：**短消息**(错误信息、命令成功提示、help)走查表式 catalog(键→多语言串)；**长文本**(gbc rules 规则集、gbc init 引导段落)按语言存独立 Markdown 资源文件、按当前语言整篇读出。资源随包分发。

## interface/
把引擎能力暴露成「人/agent 能用的形态」，并把「外部形态」与「内部实现」彻底解耦：cli、mcp、web 编辑器都只是薄表面，真正的编排、路径解析、文件读写收在 base 一处。换表面不动引擎。
命令收口为单一入口 gbc(pyproject [project.scripts])：单次执行的子命令(guarantee/dep/verify/doctor/executor/refactor/tree/doc/init/rules) + 两个常驻服务(gbc mcp up / gbc editor up)。所有面向用户的文本一律经 i18n 层产出，不硬编码。

## intent/
意图文档(gbc.md)子系统。与保证引擎(core + interface)对称：base 是唯一 IO/编排点(路径解析、gbc.md 读写、父子意图单源投影、整树读写、全树一致性)；cli(gbc doc)与 editor(web)都是薄表面，只调 base、不碰磁盘。gbc.md 解析单源复用 utils.gbc_md。
