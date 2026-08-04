# 意图
GBC 面向用户输出的多语言资源、持久偏好与语言判定。当前支持简体中文(zh)与英文(en)，默认回退 en。日常偏好由 gbc lang zh|en|auto 写入用户级纯文本语言文件（不进项目 .gbc）；判定优先级：单次显式 --lang > GBC_LANG > 持久偏好 > 系统 locale > en。两类文本分治：短消息走 catalog，长文本按语言读取 Markdown 资源。

# 文件

## lang.py
语言判定、进程内当前语言与用户级持久偏好。受支持语言从 catalog 自动发现；偏好文件仅保存语言码，可由 GBC_CONFIG_HOME 定位以便隔离测试，默认遵循用户配置目录。解析优先级：显式 > GBC_LANG > 持久偏好 > locale > en；auto 删除持久偏好。

## translate.py
翻译取值:短消息 t() 按 key 查 catalog(<lang>.json) + 长文本 load_text() 整篇读出 texts/<name>.<lang>.md。缺当前语言回退 DEFAULT_LANG,再缺回退 key 本身。
