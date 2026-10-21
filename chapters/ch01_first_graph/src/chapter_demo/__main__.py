"""命令行入口：默认运行包内样例，也可以指定本地 TXT。"""

import argparse
from contextlib import ExitStack
from importlib.resources import as_file, files
from pathlib import Path
import sys

from chapter_demo.graph import build_graph, run_plain
from chapter_demo.state import DocumentState


def main() -> int:
    parser = argparse.ArgumentParser(description="用三个节点完成 TXT 文档统计，无需模型密钥。")
    parser.add_argument("--input", type=Path, help="UTF-8 编码的 TXT 路径；默认使用包内虚构样例。")
    parser.add_argument(
        "--runner", choices=("graph", "plain"), default="graph",
        help="graph：LangGraph；plain：普通函数调用。默认 graph。",
    )
    args = parser.parse_args()

    try:
        with ExitStack() as stack:
            path = args.input
            if path is None:
                sample = files("chapter_demo").joinpath("fixtures", "travel_policy.txt")
                path = stack.enter_context(as_file(sample))
            initial_state: DocumentState = {"input_path": str(path)}
            if args.runner == "graph":
                result = build_graph().invoke(initial_state)
            else:
                result = run_plain(initial_state)
            label = "LangGraph" if args.runner == "graph" else "普通函数"
            print(f"执行方式：{label}\n\n{result['report']}")
        return 0
    except FileNotFoundError as error:
        print(f"错误：文件不存在：{error.filename}", file=sys.stderr)
    except UnicodeDecodeError:
        print("错误：文件不是有效的 UTF-8 文本，请先另存为 UTF-8。", file=sys.stderr)
    except ValueError as error:
        print(f"错误：{error}", file=sys.stderr)
    except OSError as error:
        print(f"错误：无法读取文件：{error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
