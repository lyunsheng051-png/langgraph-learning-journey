# 第 1 篇预期输出

验证日期：2026-10-21。固定样例为包内 `fixtures/travel_policy.txt`；修改样例文字后，字符数可能改变。

## LangGraph

```powershell
uv run --locked python -m chapter_demo
```

stdout：

```text
执行方式：LangGraph

文档统计结果
文件：travel_policy.txt
字符数（不含空白）：60
段落数：3
```

退出码：`0`。

## 普通函数

```powershell
uv run --locked python -m chapter_demo --runner plain
```

stdout：

```text
执行方式：普通函数

文档统计结果
文件：travel_policy.txt
字符数（不含空白）：60
段落数：3
```

退出码：`0`。首行是命令行展示信息，后面的报告由同一个格式化函数产生。

## 文件不存在

确保当前目录中没有 `missing.txt`：

```powershell
uv run --locked python -m chapter_demo --input ./missing.txt
$LASTEXITCODE
```

stderr：

```text
错误：文件不存在：missing.txt
```

退出码：`1`；stdout 为空。路径文字取决于传入路径，示例以当前 Windows 环境为准。
