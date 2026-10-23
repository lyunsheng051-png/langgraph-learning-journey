import argparse
import json
import sys
from importlib.resources import files

from langgraph.errors import GraphRecursionError

from .graph import build_graph


def repair_budget(value: str) -> int:
    number = int(value)
    if not 0 <= number <= 10:
        raise argparse.ArgumentTypeError("修正次数必须在 0—10 之间。")
    return number


def positive_integer(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("图执行上限必须大于 0。")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description="检查报告并在限定次数内修正，不调用模型。")
    parser.add_argument("--sample", choices=("draft", "complete"), default="draft")
    parser.add_argument("--max-repairs", type=repair_budget, default=2)
    parser.add_argument("--repair-mode", choices=("fix", "unchanged"), default="fix")
    parser.add_argument("--recursion-limit", type=positive_integer, default=32)
    parser.add_argument("--show-state", action="store_true")
    args = parser.parse_args()
    draft = files("chapter_demo").joinpath("fixtures", f"{args.sample}.md").read_text(encoding="utf-8")
    inputs = {"draft": draft, "max_repairs": args.max_repairs,
              "repair_mode": args.repair_mode, "logs": []}
    try:
        result = build_graph().invoke(inputs, config={"recursion_limit": args.recursion_limit})
    except GraphRecursionError:
        print(f"图执行中断：达到 recursion_limit={args.recursion_limit} 的执行上限。\n"
              "这次没有得到业务完成结果；检查循环条件，或为正常路径设置足够的图执行上限。", file=sys.stderr)
        return 3
    accepted = result["status"] == "accepted"
    output = sys.stdout if accepted else sys.stderr
    print("报告检查结果", file=output)
    print(f"状态：{'通过' if accepted else '修正次数用尽'}", file=output)
    print(f"修正次数：{result['repairs']} / {result['max_repairs']}", file=output)
    print(f"检查次数：{result['checks']}", file=output)
    print(f"剩余问题：{'、'.join(result['issues']) or '无'}", file=output)
    print(f"\n当前草稿：\n{result['draft'].strip()}", file=output)
    print("\n处理日志：", file=output)
    for index, line in enumerate(result["logs"], start=1):
        print(f"{index}. {line}", file=output)
    if args.show_state:
        print("\n最终状态：", file=output)
        print(json.dumps(result, ensure_ascii=False, indent=2), file=output)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
