# 意图
无业务语义的通用工具:`.gbc` 路径映射、json↔模型、原子写文件。被各层使用,不依赖业务层。

# 文件

## file_utils.py
`to_gbc_json_path`:源文件 → `.gbc/<dir>/gbc.<name>.json` 的**唯一映射**。base 的全局反向扫描就靠
反推这条规则把 json 路径还原成源文件。依赖 config.project(项目根)。

## json_model_operator.py
pydantic 模型 ↔ json 文件,**显式 UTF-8**(避免 Windows 默认码页乱码)。`load_model_from_json` /
`save_model_to_json`;保存经 safe_file_writer。

## safe_file_writer.py
原子写(写临时文件 → 替换)+ 备份轮转,失败回滚——保证 meta 文件不被半写损坏。
日志走 `logging.debug`(默认静默),**绝不向 stdout 打字**(stdout 是 MCP 协议通道)。

## gbc_md.py
gbc.md 文本 ↔ 结构(ParsedDoc: 意图 / 内部约束 / 有序 Entry)的 parse/serialize。gbc.md 格式(# 意图 / # 内部约束 / # 文件 下的 ## 条目)的**唯一权威解析器**:base.render_tree 与 intent-editor 工具都建立其上,不各自重写。纯文本处理、无 IO、无业务依赖。
