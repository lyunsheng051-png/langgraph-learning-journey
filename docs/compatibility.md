# 兼容与验证记录

以下列出运行验证所用的环境、依赖版本和覆盖的输入情况。

| 章节 | 验证日期 | 操作系统 | Python | LangGraph | langchain-core（传递依赖） | 模型要求 | 结果 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 第一个图 | 2026-10-21 | Windows | 3.12.11 | 1.2.16 | 1.6.12 | 无 | 正常输入、错误输入和全新副本安装运行通过 |
| 02 State 与 Reducer | 2026-10-21 | Windows | 3.12.11 | 1.2.16 | 1.6.12 | 无 | 5 项行为测试、CLI 边界与全新副本安装运行通过 |

## 第 1 篇的验证范围

验证工作目录为 `chapters/ch01_first_graph`。

| 检查 | 实际结果 |
| --- | --- |
| `uv sync --locked` | 全新副本中安装成功，使用独立新建环境 |
| `uv run --locked python -m chapter_demo` | 默认样例：60 个非空白字符、3 个段落，退出码 0 |
| `uv run --locked python -m chapter_demo --runner plain` | 与图版本报告一致，退出码 0 |
| 中文、空格路径与大写 TXT 扩展名 | 图与普通函数版本均运行成功 |
| UTF-8 BOM、CRLF、含空格或制表符的空白行 | 自制样例两种方式均得到 7 个字符、2 个段落 |
| 空文件、纯空白文件 | 均为 0 个字符、0 个段落 |
| 不存在的文件 | stderr 中文提示、stdout 为空、退出码 1 |
| 无效 UTF-8 | stderr 中文提示、stdout 为空、退出码 1 |
| 超过 1 MiB 的文件 | stderr 中文提示、stdout 为空、退出码 1 |
| 不支持的扩展名 | stderr 中文提示、stdout 为空、退出码 1 |
| 无效 runner 参数 | argparse 拒绝，退出码 2 |
| 从章节外通过 `uv run --locked --project <章节路径>` 运行 | 正确定位包内默认样例 |

验证使用自制样例与新建环境，覆盖正常输入和错误输入。平台范围为 Windows、Python 3.12.11；本记录不包含 Linux、macOS 或其他 Python 小版本的运行结果。

## 第 2 篇的验证范围

验证工作目录为 `chapters/ch02_state_reducers`。

| 检查 | 实际结果 |
| --- | --- |
| 默认累积与 `--logs append` | 样例 60 个字符、3 个段落，保留 3 条日志 |
| `--logs overwrite` | 相同统计结果，只保留最后 1 条日志，正常退出 |
| `--show-state` | 展示初始输入与最终结果；未更新字段保留，普通步骤字段覆盖为最新值 |
| `uv run --locked python -m unittest discover -s tests -v` | 5 项通过：覆盖、累积、字段保留、错误历史重复、独立运行 |
| BOM、纯空白文件、中文空格路径、大写 TXT 扩展名 | 正常运行，空白文件统计为 0 个字符、0 个段落 |
| 文件缺失、无效 UTF-8、超限、不支持的扩展名 | 中文错误，stdout 为空，退出码 1 |
| 无效日志模式 | argparse 拒绝，退出码 2 |
| 全新副本 `uv sync --locked` | 新建独立环境后安装成功 |
| 从章节外通过 `--project` 运行 | 正确定位包内样例，输出三条日志 |

验证平台为 Windows、Python 3.12.11；测试使用自制的短 TXT，不调用模型或网络服务。

## 依赖复现

前两章的直接运行依赖只有 LangGraph。langchain-core、检查点、SDK 等是安装 LangGraph 时解析得到的传递依赖；示例没有主动使用模型、检查点、网络 SDK 或追踪服务。

- Python 范围：`>=3.12,<3.13`；`.python-version` 指定 `3.12`。
- 第 1 篇声明 `langgraph>=1.0,<2.0`，第 2 篇声明 `langgraph==1.2.16`；两章各自的 `uv.lock` 均锁定为 `1.2.16`。
- 安装命令：`uv sync --locked`；运行也带 `--locked`。
- 锁文件使用阿里云公开 PyPI 镜像，安装需要能够访问该源。

首次安装可能联网。依赖安装完成后，运行前两章无需模型凭据或模型服务。
