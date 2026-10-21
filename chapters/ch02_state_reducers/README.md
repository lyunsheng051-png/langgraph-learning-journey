# LangGraph 学习之路：理解 State 与 Reducer

给三个文档处理节点分别加一条日志，对照普通字段的默认覆盖与 Reducer 的列表累积。示例无需模型密钥，各章节独立安装，不导入第 1 篇业务代码。

## 运行

使用 Python 3.12 和 uv，从仓库根目录执行：

```powershell
cd chapters/ch02_state_reducers
uv sync --locked
uv run --locked python -m chapter_demo
```

默认累积三条日志，样例统计为 60 个非空白字符、3 个段落。首次安装依赖可能联网，运行只处理本地文本，无需 `.env`。

## 对照覆盖行为

```powershell
uv run --locked python -m chapter_demo --logs overwrite
```

统计结果仍为 60 个字符、3 个段落，但只剩「已整理统计报告」一条日志。这次运行正常结束，退出码为 `0`；它演示规则与预期不符的情况，不是程序抛出异常。

恢复累积：

```powershell
uv run --locked python -m chapter_demo --logs append
```

两个模式复用相同节点与边，仅切换状态 schema 中 `logs` 的声明：

```python
logs: list[str]                       # 覆盖
logs: Annotated[list[str], add]       # 累积
```

`Annotated` 来自 `typing`，`add` 来自 `operator`。Reducer 为每个字段单独指定；`step` 在两种模式下都按默认规则替换为最新步骤「整理完成」。

## 查看状态与自定义输入

```powershell
uv run --locked python -m chapter_demo --show-state
uv run --locked python -m chapter_demo --logs overwrite --show-state
uv run --locked python -m chapter_demo --input "D:\资料\出差说明.txt"
```

`--show-state` 显示传入 `invoke` 的初始字典和返回的最终状态，不是每一步的流式输出。节点未返回的字段保持原值；替换相对路径时，以命令所在目录为准。

只支持不超过 1 MiB（1,048,576 字节）的 UTF-8 TXT，可带 BOM。字符数排除空白、保留标点；段落按空白行分隔，空文件为 0 个字符、0 个段落。

文件缺失、无效编码、超限或扩展名不支持时，stderr 输出中文错误，退出码为 `1`；无效命令行选项的退出码为 `2`。例如：

```powershell
uv run --locked python -m chapter_demo --input ./missing.txt
$LASTEXITCODE
```

确保 `missing.txt` 不存在，预期错误为「文件不存在」，退出码为 `1`。重新运行默认命令即可恢复；本章没有输出文件、数据库或检查点。

## 一个容易重复日志的写法

累积模式下，节点仅返回本次新增日志：

```python
return {"logs": ["本次新增日志"]}
```

如果返回 `state["logs"] + ["本次新增日志"]`，Reducer 会再拼接一次已有历史，导致重复。本章测试保留了这个错误实验。类似地，累积模式返回 `{"logs": []}` 不会清空历史，因为已有列表加空列表仍是原内容。

不要直接对传入状态调用 `append()`，再返回整个状态。节点通过返回字段更新表达改动；普通字典嵌套字段也不会因为用了 TypedDict 就自动深度合并。

## 代码与验证

| 文件 | 作用 |
| --- | --- |
| [state.py](src/chapter_demo/state.py) | 公共业务字段、覆盖与累积 schema |
| [graph.py](src/chapter_demo/graph.py) | 节点返回局部更新，构建同一条顺序路径 |
| [__main__.py](src/chapter_demo/__main__.py) | 模式选择、初始与最终状态展示 |
| [预期输出](examples/expected-output.md) | 两种模式的完整输出 |
| [行为测试](tests/test_state_updates.py) | 覆盖、累积、字段保留、历史重复与独立运行 |

```powershell
uv run --locked python -m unittest discover -s tests -v
```

- [第 1 篇运行指南](../ch01_first_graph/README.md)
- [仓库首页](../../README.md)
- [兼容记录](../../docs/compatibility.md)
- [常见问题](../../docs/troubleshooting.md)
