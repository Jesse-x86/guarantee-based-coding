# 意图
GBC 说明文档的离线只读查询。gbc doc list/read/search 与 MCP doc_list/doc_read/doc_search 复用 base；查询随当前版本分发的中英文手册，独立于目标项目，不读写项目意图或保证。docs/ 是手册内容单源，构建时收入包资源；--help 继续提供简短命令用法。

# 内部约束
base 负责资源读取和查询，CLI/MCP 仅收参数和呈现结果。
主题固定 quick-start/concepts/workflow/reference/onboarding-agent，不接受任意路径，不联网。list 列主题，read 返回正文，search 不区分大小写作字面检索，返回有上限的主题/行号/摘录。空查询和无效参数报错，无结果为正常结果。
支持 en/zh，复用既有语言优先级；CLI 未指定局部语言时保留根语言，MCP 单次语言不影响其他请求。docs/ 为单源，wheel 自带手册，sdist 可重建，不依赖 checkout 或 cwd。

# 文件

## base.py
手册查询只读 IO 与编排：list_topics/read_topic/search_docs，固定主题、语言选择、字面检索与有界结果。

## cli.py
gbc doc 薄 CLI：list/read/search，复用 documentation.base，裸 doc 显示帮助。

## __init__.py
离线手册查询子系统包。
