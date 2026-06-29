from pydantic import BaseModel, Field

# ============================================================================
# .gbc 元数据模型
#
# 每个代码文件对应一份 .gbc json（FileMeta），它是「双段自包含」的：
#   - provides   : 本文件作为 provider 提供的具名保证（保证为一等公民）
#   - depends_on : 本文件作为 consumer 声明的依赖边
# 两段分别承载依赖图的两个方向，由工具层负责跨文件原子地保持双向一致。
# ============================================================================


class Guarantee(BaseModel):
    """一条具名行为保证，由某个 provider 文件持有、唯一一份。

    身份 = 它在 ``FileMeta.provides`` 中的 key（一个语义化点路径 id，例如
    ``"config.llm.get_model.returns_loaded"``），**不是** 测试路径——改测试
    文件名不会改变保证的身份；多个消费者共享同一条保证时也只认这个 id。
    """

    # 承诺了什么行为、以及为何需要它（富描述，给人和 agent 读）
    desc: str

    # 测试选择器：交给 executor 做 {file} 替换的那个 str（= 旧 guarantee_path）。
    # 与 executor 分离——这里只说「跑哪个测试」，不说「怎么跑」。
    test: str

    # executor 配置名：决定「怎么跑」这个测试（命令/cwd/env/默认超时）。
    executor: str

    # 单条保证的超时覆写；-1 表示回退到 executor 的默认超时。
    timeout_override: int = -1

    # 成本秩 + 自动运行授权等级。0 = 普通，批量必跑；>=1 = 贵/慢（如需 LLM），
    # 批量 verify 中按阈值跳过并响亮报告。数字越大越「别随便跑」，高到一定
    # 程度应由人类决定是否运行。批量只跑 heavy <= 阈值的；register / 点名
    # verify_single 无视它、永远跑。
    heavy: int = 0

    # 依赖这条保证的消费者文件路径列表（多对一：一条保证可被多个文件依赖）。
    # 这是反向边；非空即代表「还有人靠着它」，退休保护据此拒绝删除。
    dependents: list[str] = Field(default_factory=list)

    # 临时停用：True 时保证的 id 与全部边（dependents/反向边）原样保留，但「出生即绿」
    # 门禁与批量 verify 都对它**暂缓执行**——不跑、不判失败、进 skipped(reason=disabled)。
    # 用途：① 重构窗口(refactor 期间测试会暂时跑不过，先 disable 守住边，改完再 enable
    #       重跑门禁)；② 循环依赖 bootstrap(测试还过不了时先占位注册)；③ 暂停在修的保证。
    # 三者本质都是「留住 id+边，但此刻先不强制测试」。disabled 是 born-green 墙上的一个
    # 洞，因此它必须**永远是响的**：check_consistency 始终把 disabled 保证及「依赖了
    # disabled 保证」的边报出来(non-empty)，tree 用 ⊘ 标记——藏不住，才不会悄悄烂掉。
    disabled: bool = False


class Dependency(BaseModel):
    """本文件（作为 consumer）声明的一条依赖边。

    ``symbol`` 写成 ``"<provider 文件>:<符号名>"``，既标明依赖了谁的哪个符号，
    也隐含了 provider 文件（取 ``:`` 前半段）。

    ``guarantees`` 列出本文件依赖的、该 provider 上的具名保证 id：
      - 空列表  = symbol 级「免费依赖」：只依赖符号存在/签名，不依赖具体行为，
                  不需要、也不创建保证与测试。
      - 非空    = 行为级依赖：每个 id 必须对应 provider ``provides`` 里的一条保证，
                  且该保证的 ``dependents`` 里登记了本文件（双向一致）。
    """

    symbol: str
    guarantees: list[str] = Field(default_factory=list)


class FileMeta(BaseModel):
    """单个代码文件的 .gbc 元数据，对 provider / consumer 两种角色都自包含。"""

    # 本文件作为 provider 提供的保证：key = 保证 id。
    provides: dict[str, Guarantee] = Field(default_factory=dict)

    # 本文件作为 consumer 声明的依赖边。
    depends_on: list[Dependency] = Field(default_factory=list)
