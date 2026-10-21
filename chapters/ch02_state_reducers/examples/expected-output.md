# 第 2 篇预期输出

默认输入为包内虚构的 `travel_policy.txt`。命令在章节目录执行。

## 累积日志

```powershell
uv run --locked python -m chapter_demo
```

```text
日志规则：累积

文档统计结果
文件：travel_policy.txt
字符数（不含空白）：60
段落数：3
当前步骤：整理完成

处理日志（3 条）：
1. 已读取：travel_policy.txt
2. 已统计：60 个非空白字符，3 个段落
3. 已整理统计报告
```

退出码为 `0`。显式指定 `--logs append` 的输出相同。

## 覆盖日志

```powershell
uv run --locked python -m chapter_demo --logs overwrite
```

```text
日志规则：覆盖

文档统计结果
文件：travel_policy.txt
字符数（不含空白）：60
段落数：3
当前步骤：整理完成

处理日志（1 条）：
1. 已整理统计报告
```

退出码为 `0`。字符与段落统计相同，区别仅在日志合并规则；普通字段 `step` 均保留最新值。

## 查看初始与最终状态

```powershell
uv run --locked python -m chapter_demo --show-state
```

报告之后附加两份 JSON。初始输入包含实际样例路径和空日志列表；最终状态包含原路径、文本、两个统计字段、报告、最新步骤和三条日志。样例绝对路径随安装目录变化，不属于固定输出。
