# 把 GBC 接到你自己的 Agent(MCP)

> 第一次接触?先看前门:**[teach-your-agent.md](./teach-your-agent.md)**。本文是其中「接 MCP」一步的展开(跨平台、自研客户端、工具清单)。

GBC 的保证能力(创建/验证保证、登记/反查依赖、一致性体检)通过一个 **MCP server** 暴露。
任何支持 [MCP](https://modelcontextprotocol.io) 的 agent(Claude Code、Cursor、自研 agent……)
都能把它作为一组工具调用。本文只讲**怎么接上**,不讲具体改代码流程。

## 它暴露哪些工具

server 名 `gbc`,stdio 传输。工具面(对应 `app/interface/mcp.py`):

| 分组 | 工具 |
|------|------|
| 保证生命周期 | `create_guarantee`（出生即绿,当场跑测,失败拒绝）、`update_guarantee`、`retire_guarantee`（仍有 dependents 则拒绝） |
| 依赖边（双向写） | `add_dependency`（给 `guarantee_id`=行为依赖,自动写反向边;不给=免费符号依赖）、`remove_dependency` |
| 读 / 反查 | `list_provides`、`list_depends_on`、`who_depends_on`（取代 grep）、`check_consistency` |
| 验证 | `verify_provider`（按 heavy 阈值三桶汇总）、`verify_guarantee`（点名单条,无视 heavy） |
| 执行器 | `upsert_executor`（定义"如何跑测试":命令模板 + cwd + 超时 + 环境变量操作） |

所有工具返回 JSON 字符串,出错统一返回 `{"error": ...}`,不抛异常给 MCP 运行时。

## 前置:在哪个 Python 环境跑

GBC 是一个独立工具,**用它自己的环境跑**(和你的目标项目环境分开)。在工具仓装依赖:

```bash
pip install -r requirements.txt   # typer[all] / pydantic / mcp
```

> 元数据存在目标项目的 `.gbc/` 下,不污染目标代码;但**进程**用 GBC 自己的解释器启动。

## 启动契约(关键)

```
python <工具仓>/serve.py <目标项目根的绝对路径>
```

两点必须照做,原因见 `serve.py` 顶部注释:

1. **目标项目根由 argv[1] 传入,不要靠环境变量。** 跨平台调用(见下)时 env 传不进去;且 server
   要把 `.gbc/` 定位到这个项目根。一个 server 实例锁定一个项目根。
2. **按绝对路径调用 `serve.py`。** 这样 `sys.path[0]` 是工具仓目录,import 到的永远是 GBC 自己的
   `app/` 包,不会被目标项目里同名的 `app/` 按 cwd 抢占。

server 走 stdio + JSON-RPC,输出强制 UTF-8。

## 接 Claude Code

项目根放一个 `.mcp.json`(项目级 MCP 配置):

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/path/to/python",
      "args": [
        "/abs/path/to/guarantee-based-coding/serve.py",
        "/abs/path/to/your-project"
      ]
    }
  }
}
```

- `command` = 跑 GBC 的解释器(装了 requirements 的那个)。
- `args[0]` = `serve.py` 绝对路径;`args[1]` = 你的项目根绝对路径。
- 重开 Claude Code 后,工具以 `mcp__gbc__*` 出现(如 `mcp__gbc__list_provides`)。

## 接任意 MCP 客户端

同样的 stdio 启动契约。多数客户端的配置就是一个 `command` + `args` 数组,形状同上。
只要客户端能 spawn 一个进程并走 stdio MCP,就能接 GBC。自研 agent 直接用对应语言的 MCP SDK
连一个 stdio server,command/args 照上面填即可。

## 跨平台:WSL 调 Windows Python(常见踩坑)

如果 agent 跑在 WSL、而 GBC 的 Python 在 Windows(如 conda env),`serve.py` 已经替你扛掉了
两个坑(env 变量传不进、cwd import 抢占),所以**只要遵守上面的启动契约即可**,无需额外设置。
配置示例(real-world):

```json
{
  "mcpServers": {
    "gbc": {
      "command": "/mnt/c/Users/<you>/miniconda3/envs/<env>/python.exe",
      "args": [
        "D:/path/to/guarantee-based-coding/serve.py",
        "D:/path/to/your-project"
      ]
    }
  }
}
```

注意:`command` 用 WSL 能看到的 `.exe` 路径(`/mnt/c/...`),而 `args` 里的路径用 **Windows 形式**
(`D:/...`),因为它们是传给 Windows 进程的 argv。同平台(纯 Linux / 纯 Windows)不需要操心这些,
直接用各自原生的绝对路径即可。

## 验证接通

接好后让 agent 调一发只读工具确认链路通:

- `check_consistency()` → 返回 `[]` 表示 `.gbc` 图一致(空项目也会返回 `[]`)。
- `list_provides("<某源文件相对路径>")` → 返回该文件已登记的保证(没有则空对象)。

> 路径参数一律用**相对项目根**的 posix 路径(如 `app/core/maker/maker.py`),不是绝对路径。

## 心智模型

- 一个 server 实例 = 一个项目根。多项目就配多个 server 条目(不同 `args[1]`)。
- MCP 只暴露**保证侧**能力。人类持有的**意图文档**(`gbc.md`)走另一条线——意图树编辑器 / 其 CLI,
  见 [intent-editor-and-skills.md](./intent-editor-and-skills.md)。
