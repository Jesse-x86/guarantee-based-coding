from pydantic import BaseModel

# 单个保证的 提出来源 和 具体保证描述
class Guarantee(BaseModel):
    source: str
    guarantee: str

# 总保证文件
class FileMeta(BaseModel):
    lang: str
    guarantees: dict[str, Guarantee]