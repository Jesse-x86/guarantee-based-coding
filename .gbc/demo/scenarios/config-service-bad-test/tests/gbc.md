# 意图
故意写错的测试：assert get_config("nonexistent") == "default"，但实际实现返回 ""。出生即绿机制当场拒绝登记，并返回完整 pytest 报错信息。
