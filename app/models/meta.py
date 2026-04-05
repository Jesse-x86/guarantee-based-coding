from pydantic import BaseModel

# 单个保证的 运行必须变量 和 具体保证描述
class Guarantee(BaseModel):
    guarantee_path: str                 # 保证对应的测试的核心文件名或其他需要插入启动命令的关键str
    guarantee_desc: str                 # 对该保证的描述，例如为何要求该保证，以及要求的是什么保证

# 总保证文件
class FileMeta(BaseModel):
    config: str
    guarantees: dict[str, list[Guarantee]]    # key: 要求该保证的项目文件