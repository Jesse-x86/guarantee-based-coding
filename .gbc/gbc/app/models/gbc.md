# 意图
所有层共享的 pydantic 模型。模型即契约:无业务逻辑、无 IO。改一个字段就是改契约,下游(core / interface / 落盘的 .gbc json)全靠它,要慎重。

# 文件

## meta.py
.gbc 元数据模型:Guarantee(具名行为保证,身份是 id≠测试路径)、Dependency(consumer 依赖边,symbol 级免费/行为级挂保证)、FileMeta(双段 provides+depends_on)。纯 pydantic,无内部依赖。

## verify.py
验证结果模型:VerifyModel(单测试原始结果)、SkippedGuarantee / VerifySummary(三桶汇总 passed/failed/skipped + green 门禁判定)。

## errors.py
异常层级,GBCError 为根,按域分(Config/Executor/Guarantee/IllegalOperation)。关键语义:GuaranteeTestFailedError(出生即绿)、GuaranteeHasDependentsError(退休保护)。表面层按类型分流渲染。
