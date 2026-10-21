# 常见问题

以下问题对应第 1 篇，命令均在 `chapters/ch01_first_graph` 中执行。

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
