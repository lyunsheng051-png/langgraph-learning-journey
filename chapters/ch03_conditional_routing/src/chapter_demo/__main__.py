"""默认样例无需额外配置，可切换文件格式观察路由。"""

import argparse
from contextlib import ExitStack
from importlib.resources import as_file, files
import json
from pathlib import Path
import sys

from chapter_demo.graph import build_graph


SAMPLES = {
    "txt": "travel_policy.txt", "docx": "travel_policy.docx", "pdf": "travel_policy.pdf",
    "empty-pdf": "no_text.pdf", "unsupported": "unsupported.md",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="按文件类型选择文本提取节点，无需模型密钥。")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--input", type=Path, help="本地 TXT、DOCX 或文本型 PDF 路径。")
    inputs.add_argument("--sample", choices=tuple(SAMPLES), default="txt", help="包内样例，默认 txt。")
    parser.add_argument("--show-state", action="store_true", help="显示最终状态中的来源片段、日志和错误。")
    args = parser.parse_args()

    with ExitStack() as stack:
        path = args.input
        if path is None:
            resource = files("chapter_demo").joinpath("fixtures", SAMPLES[args.sample])
            path = stack.enter_context(as_file(resource))
        result = build_graph().invoke({"input_path": str(path), "logs": []})
        output = sys.stdout if result["status"] == "ok" else sys.stderr
        print(result["report"], file=output)
        print("\n处理日志：", file=output)
        for index, message in enumerate(result["logs"], start=1):
            print(f"{index}. {message}", file=output)
        if args.show_state:
            print("\n最终状态：", file=output)
            print(json.dumps(result, ensure_ascii=False, indent=2), file=output)
        return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
