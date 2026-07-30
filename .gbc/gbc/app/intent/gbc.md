# 意图
意图文档(gbc.md)子系统。与保证引擎(core + interface)对称：base 是唯一 IO/编排点(路径解析、gbc.md 读写、父子意图单源投影、整树读写、全树一致性)；cli(gbc doc)、mcp(经 interface.mcp 暴露的 doc 工具)与 editor(web)都是薄表面，只调 base、不碰磁盘。意图读(show/check)与写(set-*/sync/migrate)都可经 MCP，写入的人类确认闸门由用户 agent 框架承担。gbc.md 解析单源复用 utils.gbc_md。

# 内部约束
- base 是唯一碰 gbc.md 磁盘的地方；cli/editor 表面零 IO、零路径解析。
- gbc.md 的父子一致性是确定性约束，只经 base 的操作维护——绝不手编。
- 子文件夹意图是单一事实源，父条目为投影(set_intent 自动投影)。
- 领域错误走 GBCError 体系(IntentDocError)并经 i18n，不裸抛 ValueError。

# 文件

## base.py
意图文档子系统的编排/IO 总线——唯一碰 gbc.md 磁盘处。路径解析(.gbc 镜像层)、单文档读写、父子投影、单文档操作(set_intent/set_constraints/set_file/rm_entry/show)、整树读写(read_tree/write_tree 供 web)、全树一致性(check/sync/migrate)。

## cli.py
gbc doc 命令的薄表面：show/set-intent/set-constraints/set-file/rm-entry/check/sync/migrate，只调 intent.base。

## editor.py
意图编辑器 web 表面：HTTP handler 只调 intent.base 的 resolve_gbc/read_tree/write_tree，自身不解析路径不拼 gbc.md。前端静态页在 gbc/assets/editor/（经 app.assets 定位）。
