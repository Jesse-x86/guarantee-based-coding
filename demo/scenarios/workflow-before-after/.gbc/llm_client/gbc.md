# 意图

本目录只放 **LLM 调用**（组 prompt、调模型、解析模型输出）。不负责读配置文件、环境变量或密钥。

# 内部约束

- 禁止在此目录新增配置 IO（读 yaml/json/env 取密钥等）
- 配置与密钥从 `config/` 注入，由调用方传入

# 文件

- `client.py`：对外 `chat(prompt) -> str`
