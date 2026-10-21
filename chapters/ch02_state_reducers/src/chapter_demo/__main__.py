"""命令行选择累积或覆盖，并按需查看本次运行前后的状态。"""

import argparse
from contextlib import ExitStack
from importlib.resources import as_file, files
import json
from pathlib import Path
import sys

from chapter_demo.graph import build_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="比较 State 默认覆盖与 Reducer 日志累积，无需模型密钥。")
    parser.add_argument("--input", type=Path, help="UTF-8 TXT 路径，默认使用包内样例。")
    parser.add_argument("--logs", choices=("append", "overwrite"), default="append", help="日志规则，默认 append（累积）。")
    parser.add_argument("--show-state", action="store_true", help="显示传给图的初始输入和 invoke 返回的最终状态。")
    args = parser.parse_args()

    try:
        with ExitStack() as stack:
            path = args.input
            if path is None:
                sample = files("chapter_demo").joinpath("fixtures", "travel_policy.txt")
                path = stack.enter_context(as_file(sample))
            initial_state = {"input_path": str(path), "logs": []}
            result = build_graph(args.logs).invoke(initial_state)
            label = "累积" if args.logs == "append" else "覆盖"
            print(f"日志规则：{label}\n\n{result['report']}")
            print(f"当前步骤：{result['step']}\n")
            print(f"处理日志（{len(result['logs'])} 条）：")
            for index, entry in enumerate(result["logs"], start=1):
                print(f"{index}. {entry}")
            if args.show_state:
                print("\n初始输入：")
                print(json.dumps(initial_state, ensure_ascii=False, indent=2))
                print("最终状态：")
                print(json.dumps(result, ensure_ascii=False, indent=2))
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
