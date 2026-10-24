import argparse
import json
import sys
from importlib.resources import files

from .graph import build_graph
from .model_adapter import DeepSeekSummaryClient, MockSummaryClient, SummaryContext
from .settings import ConfigurationError, Settings


def main():
    parser = argparse.ArgumentParser(description="生成并校验文档摘要；默认固定响应 mock，不调用模型。")
    parser.add_argument("--mode", choices=("mock", "real"), default="mock")
    parser.add_argument("--mock-case", choices=("success", "missing-field", "invalid-json", "timeout", "refusal", "truncated"))
    parser.add_argument("--input", help="UTF-8 TXT 路径；mock 仅支持内容与包内样例一致的资料")
    parser.add_argument("--show-state", action="store_true")
    args = parser.parse_args()
    if args.mode == "real" and args.mock_case is not None:
        parser.error("--mock-case 只适用于 mock 模式。")
    try:
        if args.mode == "real":
            client = DeepSeekSummaryClient(Settings.from_env())
        else:
            client = MockSummaryClient(args.mock_case or "success")
    except ConfigurationError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    path = args.input or str(files("chapter_demo").joinpath("fixtures", "travel_policy.txt"))
    result = build_graph().invoke({"input_path": path, "logs": []},
                                 config={"recursion_limit": 16}, context=SummaryContext(client=client))
    accepted = result["status"] == "accepted"
    output = sys.stdout if accepted else sys.stderr
    print("文档摘要结果", file=output)
    print(f"模式：{'mock（固定响应，未调用模型）' if args.mode == 'mock' else 'real（DeepSeek）'}", file=output)
    if accepted:
        print(f"摘要：{result['summary']['summary']}", file=output)
        print("关键事项：", file=output)
        for index, point in enumerate(result["summary"]["key_points"], start=1):
            print(f"{index}. {point}", file=output)
    else:
        print(f"状态：未接受摘要\n原因：{result['error']}", file=output)
    print("\n处理日志：", file=output)
    for index, line in enumerate(result["logs"], start=1):
        print(f"{index}. {line}", file=output)
    if args.show_state:
        print("\n最终状态（包含资料和原始响应）：", file=output)
        print(json.dumps(result, ensure_ascii=False, indent=2), file=output)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
