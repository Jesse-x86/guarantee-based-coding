# 意图
GBC 面向用户输出的多语言资源与语言判定。当前支持简体中文(zh)与英文(en)，默认回退 en(发布英文优先)。语言判定优先级：显式 --lang > 环境变量 GBC_LANG > 系统 locale > en。
两类文本分治：**短消息**(错误信息、命令成功提示、help)走查表式 catalog(键→多语言串)；**长文本**(gbc rules 规则集、gbc setup 接线指南)按语言存独立 Markdown 资源文件、按当前语言整篇读出。资源随包分发。

# 文件

## lang.py
语言判定 + 从文件自动发现受支持语言。扫描 catalog 目录推导支持的语言列表,判定优先级:显式 lang > GBC_LANG > 系统 locale > 默认 en。

## translate.py
翻译取值:短消息 t() 按 key 查 catalog(<lang>.json) + 长文本 load_text() 整篇读出 texts/<name>.<lang>.md。缺当前语言回退 DEFAULT_LANG,再缺回退 key 本身。
