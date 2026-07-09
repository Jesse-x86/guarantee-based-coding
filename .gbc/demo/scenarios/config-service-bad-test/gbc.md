# 意图

# 文件

## scenario.json
错误测试剧本 JSON。project: config-service。步骤：show provider → show 错误测试 → create_guarantee（被拒，展示 pytest 断言失败详情）→ 解释出生即绿。

## tests/
故意写错的测试：assert get_config("nonexistent") == "default"，但实际实现返回 ""。出生即绿机制当场拒绝登记，并返回完整 pytest 报错信息。
