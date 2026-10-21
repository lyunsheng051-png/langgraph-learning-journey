# 第 1 篇：第一个 LangGraph

把三个普通 Python 函数连成工作流：读取 TXT → 统计字符与段落 → 格式化结果。无需模型密钥，不调用任何模型服务。

## 运行

需要 Python 3.12 和 uv。下面的 PowerShell 命令从代码仓库根目录开始执行：

```powershell
cd chapters/ch01_first_graph
uv sync --locked
uv run --locked python -m chapter_demo
```

首次安装依赖可能联网；安装完成后，本章业务运行无需模型服务，不需要 `.env`。

默认读取随 Python 包分发的虚构出差资料，使用包资源定位，不依赖调用者恰好在样例所在目录。

对照普通函数调用：

```powershell
uv run --locked python -m chapter_demo --runner plain
```

两种方式复用同样的三个函数，统计结果相同，首行的执行方式不同。普通函数版本显式合并返回字典，图版本由 LangGraph 应用节点返回的更新；后续篇目再解释 Reducer 等合并规则。

## 自己的 TXT

```powershell
uv run --locked python -m chapter_demo --input "D:\资料\出差说明.txt"
```

替换为实际存在的文件；含空格的路径加引号。相对路径相对于运行命令时的工作目录；文件使用 UTF-8 编码，可包含 BOM。只支持 `.txt`（大小写均可），最多 1 MiB（1,048,576 字节）。

统计规则：

- 字符数排除所有空白字符，保留标点和数字；使用 Python 字符串的字符计数，不是中文分词、英文单词数或 token 数。
- 段落以一个或多个空白行分隔；段落内的单个换行不另算一段。
- 空文件和纯空白文件均为 0 个字符、0 个段落。

## 失败实验：不存在的文件

在章节目录中执行，确保该文件不存在：

```powershell
uv run --locked python -m chapter_demo --input ./missing.txt
$LASTEXITCODE
```

预期 stderr：

```text
错误：文件不存在：missing.txt
```

预期退出码为 `1`，且不会显示统计结果。路径显示可能因传入形式不同而变化。CLI 捕获文件读取异常并提示原因；这次失败发生在读取节点，与图编译失败是不同的问题。

再运行默认命令即可恢复正常。程序只在终端打印结果，不创建输出文件、数据库或检查点，无需重置业务数据。

其他边界：不支持的扩展名、超过大小限制、无效 UTF-8 会返回中文错误和退出码 `1`。参数错误由 argparse 提示，退出码为 `2`。文件夹、无权限等系统读取错误也会返回退出码 `1`，具体消息由操作系统决定。

## 代码入口

| 文件 | 作用 |
| --- | --- |
| [state.py](src/chapter_demo/state.py) | 声明输入路径和逐步产生的业务字段 |
| [graph.py](src/chapter_demo/graph.py) | 三个节点、图的构建和普通函数对照 |
| [__main__.py](src/chapter_demo/__main__.py) | 命令行参数、样例资源和错误提示 |
| [travel_policy.txt](src/chapter_demo/fixtures/travel_policy.txt) | 自制虚构样例，随包分发 |
| [expected-output.md](examples/expected-output.md) | 实际验证后记录的预期输出 |

执行顺序：

```text
START → read_document → analyze_document → format_report → END
```

`START` 和 `END` 是图的起止标记。`compile()` 生成可执行图；`invoke()` 才开始本次处理。节点返回需要更新的字段，不需要返回整个状态。

TypedDict 用于描述字典字段，不会自动读取文件、填充默认值或完成运行时参数校验。本章的 `NotRequired` 表示该字段可以暂时不出现在状态中；错误输入由读取逻辑和 CLI 明确处理。

## 小练习

在格式化节点增加一行「平均每段字符数」，使用已有统计值计算；空文件时显示 `0`，不要出现除零错误。无需增加新节点或依赖。

## 验证记录与导航

具体依赖、验证时间和运行结果见[兼容记录](../../docs/compatibility.md)。本章依赖范围由 pyproject 声明，实际安装版本以 `uv.lock` 为准。执行命令中的 `--locked` 用来避免运行时悄悄重写锁文件。

- [返回仓库首页](../../README.md)
- [常见问题](../../docs/troubleshooting.md)
- [更新记录](../../docs/maintenance.md)
