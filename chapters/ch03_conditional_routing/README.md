# LangGraph 学习之路：用条件边选择下一步

同一条工作流按扩展名选择 TXT、DOCX 或 PDF 提取节点，拿到统一文本片段后再统计。日志使用上一章的累积规则；本章无需模型密钥。

## 运行

从仓库根目录执行：

```powershell
cd chapters/ch03_conditional_routing
uv sync --locked
uv run --locked python -m chapter_demo
uv run --locked python -m chapter_demo --sample docx
uv run --locked python -m chapter_demo --sample pdf
```

使用 Python 3.12。首次安装依赖可能联网，默认样例已随包提供，运行不需要额外生成文件或访问模型服务。

## 观察结束路径

```powershell
uv run --locked python -m chapter_demo --sample unsupported
$LASTEXITCODE
uv run --locked python -m chapter_demo --sample empty-pdf
$LASTEXITCODE
```

两种情况均返回退出码 `1`，提示与处理日志写入 stderr，stdout 为空。无文本样例是一页空白 PDF，用于演示没有可提取文本；它不代表所有扫描件，也不会触发 OCR。不支持格式在提取前结束，无文本 PDF 在提取后结束，两者都不会进入统计节点。

成功输入返回退出码 `0`，无效命令行选项返回 `2`。重新运行默认命令即可重试，没有输出文件或业务数据库需要重置。

## 自定义文件与来源

```powershell
uv run --locked python -m chapter_demo --input "D:\资料\出差说明.docx"
uv run --locked python -m chapter_demo --sample pdf --show-state
```

`--input` 与 `--sample` 互斥，相对路径以当前工作目录为准。扩展名大小写不影响分流，但改名不等于转换内容，格式损坏会进入提取失败路径。

| 格式 | 提取范围 | 一个文本片段对应什么 |
| --- | --- | --- |
| TXT | UTF-8 文本，可带 BOM | 按空白行分隔的非空段落，记录段落编号 |
| DOCX | document.paragraphs 中的非空正文段落 | 原段落编号，空段落不输出；不读取表格、页眉、图片 |
| PDF | pypdf 能提取的文本层 | 一个有文本的页，记录原 PDF 页码；无可提取文本的页跳过 |

字符数排除空白、保留标点。片段数不是统一的段落数：PDF 的一页可能包含多个自然段，DOCX 也不提供稳定页码。本章不做版式还原。混合 PDF 中只有图片的页也不会被 OCR，结果只包含实际提取到的文本。

输入文件最多 1 MiB，PDF 最多 20 页，提取文本最多 100,000 字符，DOCX 声明的解压内容最多 8 MiB。加密 PDF、无文本文件、无效 UTF-8 和损坏格式给出明确提示。限制面向本地小型教学资料，不是任意外部文件的通用解析服务。

## 路由与代码

```text
START → 检查输入 → 条件边 → TXT / DOCX / PDF 提取（选择一个）
                   ↓                  ↓
                结束提示          提取后条件边
                                  ↓       ↓
                                统计    结束提示
                                  ↓       ↓
                                报告      END
                                  ↓
                                 END
```

`route_by_type()` 返回逻辑标签，`add_conditional_edges()` 的映射把标签对应到节点名。路由函数不读取文档、不修改状态。三个提取节点是可选分支，不是并行分发。

| 文件 | 作用 |
| --- | --- |
| [graph.py](src/chapter_demo/graph.py) | 输入检查、条件边、统一统计和结束路径 |
| [extractors.py](src/chapter_demo/extractors.py) | 格式提取与输入限制 |
| [state.py](src/chapter_demo/state.py) | 状态、来源片段、累积日志 |
| [预期输出](examples/expected-output.md) | 正常与失败样例的实际结果 |
| [行为测试](tests/test_routing.py) | 分支选择、失败不进入统计、来源定位和独立运行 |

```powershell
uv run --locked python -m unittest discover -s tests -v
```

自制样例可以通过生成脚本重建，只有这个操作才需要额外的 reportlab 依赖组：

```powershell
uv run --locked --group fixtures python scripts/create_fixtures.py
```

生成内容包括一份 DOCX、一份文本层 PDF 与一份空白 PDF；TXT 和 Markdown 样例直接保存在 fixtures 中。

- [第 2 篇](../ch02_state_reducers/README.md)
- [仓库首页](../../README.md)
- [兼容记录](../../docs/compatibility.md)
- [常见问题](../../docs/troubleshooting.md)
