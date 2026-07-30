# 意图
无业务语义的通用工具:.gbc 路径映射、json↔模型、原子写文件。被各层使用,不依赖业务层。

# 文件

## gbc_md.py
gbc.md 文档解析器(意图 / 约束 / 文件条目的结构化解析)。意图文档子系统的单源解析入口。

## safe_file_writer.py
原子文件写入:先写临时、再 rename,带备份轮转。所有 .gbc 落盘经此通道。

## json_model_operator.py
Pydantic 模型 ↔ JSON 文件的序列化/反序列化。load_model_from_json / save_model_to_json。

## file_utils.py
通用文件路径工具:.gbc 目录映射(源码路径 → .gbc/<path>/ 镜像)、POSIX 路径规范化。
