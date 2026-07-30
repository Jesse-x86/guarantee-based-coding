# 意图
无业务语义的通用工具:.gbc 路径映射、json↔模型、原子写文件。被各层使用,不依赖业务层。

# 文件

## gbc_md.py
gbc.md 文档解析器(意图 / 约束 / 文件条目的结构化解析)。意图文档子系统的单源解析入口。

## safe_file_writer.py
原子文件写入:先写临时、再 rename,带备份轮转。保证元数据(.gbc/**/*.json)经此通道落盘;意图文档(gbc.md)的落盘是直接 write_text,不经过本文件。

## json_model_operator.py
Pydantic 模型 ↔ JSON 文件的序列化/反序列化。load_model_from_json / save_model_to_json。

## file_utils.py
通用文件路径工具:.gbc 目录映射(源码路径 → .gbc/<path>/ 镜像,产出对应的 gbc.<name>.json 路径)。POSIX 路径规范化(as_posix)由调用方(interface/intent 的 base 层)各自处理,不在本文件。
