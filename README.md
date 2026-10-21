# langgraph-learning-journey
记录我学习和实践 LangGraph 的过程。从状态、节点和边开始，逐步探索工具调用、流程分支、状态持久化与人工确认，动手完成一个 AI 应用。分享可运行的代码、遇到的问题，以及解决问题时的思考，供同样在学习的你参考。

## 从这里开始

专题名称：**LangGraph 学习之路：从第一个节点到完整 AI 工作流**。

面向具备 Python 基础的读者，通过同一个「文档资料助手」学习 LangGraph，从节点和状态开始，逐步理解一个 AI 工作流怎样执行。

前两篇从普通 Python 函数、图和状态更新入手，不需要模型密钥。

从仓库根目录运行第 1 篇：

```powershell
cd chapters/ch01_first_graph
uv sync --locked
uv run --locked python -m chapter_demo
```

使用 Python 3.12 和 uv。默认样例输出 60 个非空白字符、3 个段落；本篇不调用模型服务。

## 学习路线

| 阶段 | 篇目 | 目标 |
| --- | --- | --- |
| 理解图的执行 | 01—04 | 节点与边、状态更新、条件路由、有界循环 |
| 接入模型与工具 | 05—08 | 结构化摘要、工具循环、有依据的问答、并行处理 |
| 展示、保存与恢复 | 09—12 | 进度、检查点、人工确认、记忆作用域 |
| 整理与交付 | 13—16 | 子图、故障实验、本地 API、完整复现 |

## 章节目录

| 篇号 | 主题 | 代码 |
| --- | --- | --- |
| 01 | 我学 LangGraph 的第一步：把三个函数连成工作流 | [运行指南](chapters/ch01_first_graph/README.md) |
| 02 | LangGraph 学习之路：理解 State 与 Reducer | [运行指南](chapters/ch02_state_reducers/README.md) |

各章节独立维护环境和锁文件，进入对应目录运行，不需要安装其他章节。

## 运行记录与反馈

- [兼容与验证记录](docs/compatibility.md)
- [常见问题](docs/troubleshooting.md)
- [更新记录](docs/maintenance.md)

反馈问题时，请注明篇号、运行命令、Python 与依赖版本、错误信息，避免附带真实密钥和私人资料。示例资料为自制虚构内容。

代码使用 [MIT 许可证](LICENSE)。
