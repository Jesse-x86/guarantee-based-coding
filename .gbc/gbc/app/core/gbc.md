# 意图
保证系统的核心逻辑与"怎么真的把测试跑起来"。纯模型操作:不解析路径、不读写 .gbc 文件(那是 base 的活)。进出本层的文件路径一律是项目相对字符串。

# 文件

## guarantee.py
保证的核心逻辑(CRUD + 出生即绿门禁 + 退休保护)。纯模型操作,不收文件路径(字符串),交给 base 落盘。

## executor.py
执行器:把"跑一条测试"抽象成子进程调用,收 command + env_ops + timeout,产出 VerifyModel。语言无关。

## env.py
环境变量操作(EnvAction 的 set/append/prepend/remove)。被 executor 用于构建子进程环境。
