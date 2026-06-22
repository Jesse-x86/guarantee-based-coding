# utils —— 横切支撑

无业务语义的通用工具:`.gbc` 路径映射、json↔模型、原子写文件。被各层使用,不依赖业务层。

## file_utils.py

`to_gbc_json_path`:源文件 → `.gbc/<dir>/gbc.<name>.json` 的**唯一映射**。base 的全局反向扫描就靠
反推这条规则把 json 路径还原成源文件。依赖 config.project(项目根)。

## json_model_operator.py

pydantic 模型 ↔ json 文件,**显式 UTF-8**(避免 Windows 默认码页乱码)。`load_model_from_json` /
`save_model_to_json`;保存经 safe_file_writer。

## safe_file_writer.py

原子写(写临时文件 → 替换)+ 备份轮转,失败回滚——保证 meta 文件不被半写损坏。
日志走 `logging.debug`(默认静默),**绝不向 stdout 打字**(stdout 是 MCP 协议通道)。
