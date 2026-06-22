from pydantic import BaseModel, Field

# ============================================================================
# 验证结果模型
#
# 分两层：
#   - VerifyModel    : 单个测试跑完的「原始结果」（由 core/executor 直接产出）。
#   - VerifySummary  : 一次批量 verify 的「三桶汇总」，门禁判定从它读出。
#
# 门禁是二元的：跑了的测试只有 过(green) / 挂(red)；没跑的测试不是「一种结果」
# 而是「缺席」（heavy 跳过）。所以 skipped 不染红，green = (failed 为空)。
# ============================================================================


class VerifyModel(BaseModel):
    """单个测试跑完的原始结果。"""

    return_code: int
    stdout: None | str
    stderr: None | str


class SkippedGuarantee(BaseModel):
    """一条被跳过、未运行的保证（当前只因 heavy 超过运行阈值）。"""

    id: str
    heavy: int
    reason: str = "heavy"


class VerifySummary(BaseModel):
    """一次（批量）verify 的三桶汇总 + 门禁判定。

    passed / failed / skipped 三个桶按保证 id 分类；``results`` 保留真正跑过的
    保证的原始输出，供失败时排查。skipped 必须被响亮报告（"X heavy skipped"），
    让调用方知道「即便全绿，问题也可能出在这些没跑的保证上」。
    """

    passed: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    skipped: list[SkippedGuarantee] = Field(default_factory=list)

    # 真正跑过的保证 id -> 原始结果（passed/failed 都收，skipped 不收）。
    results: dict[str, VerifyModel] = Field(default_factory=dict)

    @property
    def green(self) -> bool:
        """门禁是否通过：没有任何失败即为绿（skipped 不影响）。"""
        return not self.failed
