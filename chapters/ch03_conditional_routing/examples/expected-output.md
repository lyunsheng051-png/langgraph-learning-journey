# 第 3 篇预期输出

样例文字为自制虚构内容，三种格式均包含 60 个非空白字符。TXT、DOCX 采用段落片段，PDF 采用页面片段。

## 默认 TXT

```powershell
uv run --locked python -m chapter_demo
```

```text
文档提取结果
文件：travel_policy.txt
提取方式：TXT
字符数（不含空白）：60
文本片段数：3
来源位置：第 1 段、第 2 段、第 3 段

处理日志：
1. 已检查：travel_policy.txt
2. 已提取（TXT）：3 个文本片段
3. 已统计：60 个非空白字符
4. 已整理提取结果
```

退出码为 `0`。运行 `--sample docx` 时，文件名变为 `travel_policy.docx`，提取方式及日志标签为 `DOCX`；字符数、片段数与段落编号相同。

## 文本 PDF

```powershell
uv run --locked python -m chapter_demo --sample pdf
```

```text
文档提取结果
文件：travel_policy.pdf
提取方式：PDF
字符数（不含空白）：60
文本片段数：1
来源位置：第 1 页

处理日志：
1. 已检查：travel_policy.pdf
2. 已提取（PDF）：1 个文本片段
3. 已统计：60 个非空白字符
4. 已整理提取结果
```

退出码为 `0`。

## 无文本 PDF

```powershell
uv run --locked python -m chapter_demo --sample empty-pdf
```

stderr：

```text
文档处理失败
文件：no_text.pdf
原因：未提取到可处理文本；本章不提供 OCR，也不处理 DOCX 表格或图片。

处理日志：
1. 已检查：no_text.pdf
2. 提取失败（PDF）：未提取到可处理文本；本章不提供 OCR，也不处理 DOCX 表格或图片。
3. 已结束：本次输入无法处理
```

stdout 为空，退出码为 `1`。

## 不支持的类型

```powershell
uv run --locked python -m chapter_demo --sample unsupported
```

stderr：

```text
文档处理失败
文件：unsupported.md
原因：不支持文件类型：md；仅支持 TXT、DOCX、PDF。

处理日志：
1. 已检查：unsupported.md
2. 已结束：本次输入无法处理
```

stdout 为空，退出码为 `1`。这条路径没有执行文本提取或统计。
