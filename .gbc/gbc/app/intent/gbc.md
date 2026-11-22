# 意图
意图文档(gbc.md)子系统。与保证引擎(core + interface)对称：base 是唯一 IO/编排点(路径解析、gbc.md 读写、父子意图单源投影、整树读写、全树一致性)；cli(gbc intent)、mcp(经 interface.mcp 暴露的 intent_* 工具)与 editor(web)都是薄表面，只调 base、不碰磁盘。意图读(show/check)与写(set-*/sync/migrate)都可经 MCP，写入的人类确认闸门由用户 agent 框架承担。gbc.md 解析单源复用 utils.gbc_md。

# 内部约束
- base 是唯一碰 gbc.md 磁盘的地方；cli/editor 表面零 IO、零路径解析。
- gbc.md 的父子一致性是确定性约束，只经 base 的操作维护——绝不手编。
- 子文件夹意图是单一事实源，父条目为投影(set_intent 自动投影)。
- 领域错误走 GBCError 体系(IntentDocError)并经 i18n，不裸抛 ValueError。
- 编辑器可只读展示文件条目的 .gbc json(provides/depends_on,经 file_meta_view)，但绝不提供写入——.gbc 的写永远只属保证引擎。

# 文件

## base.py
意图文档子系统的编排/IO 总线——唯一碰 gbc.md 磁盘处。提供路径解析、单文档操作与父子意图投影、嵌套树读写、供 web 编辑器使用的项目语义 flat 树，以及冲突感知的选择性保存：按字段三方合并当前内存/加载快照/硬盘状态，只写变化的 gbc.md，保留无关外部改动，删除文件夹意图子树时不碰源码与 .gbc json。另提供文件条目 .gbc json 只读视图及全树一致性(check/sync/migrate)。

## cli.py
gbc intent 薄表面：show/set-intent/set-constraints/set-file/rm-entry/check/sync/migrate，只调 intent.base，不保留旧 doc 别名。

## editor.py
意图编辑器 web 薄表面：HTTP handler 只负责参数收发并调用 intent.base，不自行解析 gbc.md 或写磁盘。暴露项目语义 flat 树读取、冲突感知选择性保存、文件条目 .gbc json 只读视图与语言配置；旧的整树盲写 HTTP 入口已关闭。前端位于 gbc/assets/editor/，采用原生 ES modules 与分层 CSS、零框架零构建，提供中英 i18n、文件夹/文件一等节点、当前/加载时/硬盘三态 diff、文本复制/下载、回退与冲突确认。
