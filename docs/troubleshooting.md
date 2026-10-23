# 常见问题

## 第 4 篇：有次数限制，为什么还会触发 GraphRecursionError？

`max_repairs` 是业务上的修正次数，`recursion_limit` 是单次图执行的 super-step 上限。初始化、检查、修正和结束都需要执行步骤。图上限设得过小，正常的有界流程也来不及结束。

先确认路由包含通过和预算耗尽两种出口，再为正常路径设置足够上限。本章默认 32；`--recursion-limit 3` 是刻意触发中断的实验，退出码为 3。`recursion_limit` 放在调用配置顶层，不放入 `configurable`。

`--max-repairs 1` 和 `--repair-mode unchanged` 走业务停止分支，退出码为 1，会保留草稿和问题列表。这里的无效修正是正常返回原文，不是节点异常自动重试。

通用问题适用于前三篇，命令在对应章节目录执行；从仓库根目录运行时可通过 `--project` 指定章节。

## 提示找不到 chapter_demo

使用章节目录下的 uv 环境运行，不要直接调用其他 Python 环境：

```powershell
uv sync --locked
uv run --locked python -m chapter_demo
```

从仓库根目录运行时，也可以显式指定项目：

```powershell
uv run --locked --project ./chapters/ch01_first_graph python -m chapter_demo
```

## 文件明明存在，却提示不存在

`--input` 的相对路径以当前工作目录为准。可以改用绝对路径，并为包含空格的路径加引号。默认包内样例不受这个相对路径问题影响。

## TXT 提示不是有效的 UTF-8

扩展名不代表文本编码。将文件另存为 UTF-8 后重试；本章支持 UTF-8 BOM，不自动猜测 GBK 等编码，也不忽略解码错误。

## 统计数量与编辑器不同

本章字符数排除所有空白字符、包含标点；按 Python 字符串计数，不做中文分词，不计算 token。段落按空白行分隔，单个换行仍可属于同一段。虚构样例的标题也是一段，因此默认结果是 60 个字符、3 个段落。

## Windows 管道捕获中文乱码

Windows 下通过管道捕获输出时，如果中文出现乱码，可以在当前 PowerShell 会话启用 Python UTF-8 模式后重试：

```powershell
$env:PYTHONUTF8 = "1"
uv run --locked python -m chapter_demo
```

这影响 Python 文本流的编码选择，不修改输入文件。输入 TXT 仍由程序明确按 UTF-8 读取。

## uv 提示无法 hardlink，改为 copy

缓存与项目目录无法建立硬链接时，uv 会改用复制。若复制可正常完成，无需重装环境；也可以明确指定复制模式：

```powershell
uv sync --locked --link-mode copy
```

## 为什么会安装 langchain-core 等包？

它们是 LangGraph 的传递依赖，不代表本章调用了模型。无需为此设置 API Key 或 `.env`。

## 实验后怎样重置？

第 1 篇没有数据库、检查点或输出文件。失败实验结束后重新运行默认命令即可；若手动修改源码或样例，恢复修改后再运行。不要把删除整章目录当作重置方式。

## 第 2 篇：三个节点都执行了，为什么只有一条日志？

`--logs overwrite` 使用普通列表字段，每个节点返回的 `logs` 都覆盖旧值，最后只剩格式化节点的日志。切换为累积规则：

```powershell
uv run --locked python -m chapter_demo --logs append
```

本例中各节点只返回本次新增日志。若手动修改成返回整份历史，累积 Reducer 会再次拼接旧记录，导致重复。改回返回新增内容后重新运行即可；第 2 篇也没有持久化业务数据。

## 第 3 篇：文件扩展名支持，为什么还是提取失败？

扩展名仅决定使用哪个解析器，文件内容仍需符合格式。重命名后缀不会完成格式转换；加密或损坏的 PDF、损坏的 DOCX 都可能无法处理。

无文本 PDF 不会自动进行 OCR；DOCX 示例只读取正文段落。图把这些情况转成明确原因并结束，不继续统计。可以先用 `--sample txt`、`--sample docx` 或 `--sample pdf` 对照包内正常样例。

## 第 3 篇：为什么相同内容的片段数不同？

TXT 与 DOCX 按段落输出片段，PDF 按有文本的页输出片段。同一页 PDF 可以包含多个自然段，因此本章显示「文本片段数」。来源编号保留原位置，跳过空段落或无文本页后可能不连续。
