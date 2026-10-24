import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch

import httpx
from langchain_core.messages import AIMessage

from chapter_demo.graph import build_graph
from chapter_demo.model_adapter import DeepSeekSummaryClient, MockSummaryClient, SummaryContext
from chapter_demo.settings import ConfigurationError, Settings


FIXTURES = files("chapter_demo").joinpath("fixtures")


class ResponseClient:
    def __init__(self, content, metadata=None):
        self.content = content
        self.metadata = metadata or {}
        self.calls = 0
        self.messages = None
        self.config = None

    def invoke(self, messages, *, config):
        self.calls += 1
        self.messages, self.config = messages, config
        return AIMessage(content=self.content, response_metadata=self.metadata)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_graph()
        self.temp = tempfile.TemporaryDirectory(prefix="summary-tests-")
        self.root = Path(self.temp.name).resolve()
        assert self.root.parent == Path(tempfile.gettempdir()).resolve()
        self.addCleanup(self.temp.cleanup)

    def run_graph(self, client=None, path=None):
        return self.graph.invoke(
            {"input_path": str(path or FIXTURES.joinpath("travel_policy.txt")), "logs": []},
            config={"recursion_limit": 16, "tags": ["local-test"]},
            context=SummaryContext(client=client or MockSummaryClient()),
        )

    def test_mock_success_preserves_structured_values(self):
        result = self.run_graph()
        expected = json.loads(FIXTURES.joinpath("success.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["summary"], expected)
        self.assertEqual(len(result["logs"]), 4)

    def test_missing_field_identifies_its_location(self):
        result = self.run_graph(MockSummaryClient("missing-field"))
        self.assertEqual(result["status"], "rejected")
        self.assertIn("key_points (missing)", result["error"])
        self.assertEqual(result["summary"], {})
        self.assertNotIn("已接受摘要", result["logs"])

    def test_malformed_json_is_not_silently_completed(self):
        result = self.run_graph(MockSummaryClient("invalid-json"))
        self.assertEqual(result["status"], "rejected")
        self.assertIn("JSON (json_invalid)", result["error"])

    def test_schema_rejects_empty_wrong_type_extra_and_oversize_fields(self):
        cases = [
            {"summary": "   ", "key_points": ["事项"]},
            {"summary": "摘要", "key_points": []},
            {"summary": "摘要", "key_points": "事项"},
            {"summary": "摘要", "key_points": [123]},
            {"summary": "摘要", "key_points": [" "]},
            {"summary": "摘要", "key_points": ["事项"] * 6},
            {"summary": "长" * 201, "key_points": ["事项"]},
            {"summary": "摘要", "key_points": ["长" * 101]},
            {"summary": "摘要", "key_points": ["事项"], "extra": True},
        ]
        for value in cases:
            with self.subTest(value=value):
                result = self.run_graph(ResponseClient(json.dumps(value, ensure_ascii=False)))
                self.assertEqual(result["status"], "rejected")
                self.assertEqual(result["summary"], {})

    def test_whitespace_is_trimmed_in_valid_fields(self):
        result = self.run_graph(ResponseClient('{"summary":" 摘要 ","key_points":[" 事项 "]}'))
        self.assertEqual(result["summary"], {"summary": "摘要", "key_points": ["事项"]})

    def test_timeout_refusal_and_truncation_do_not_reach_validator(self):
        for case in ("timeout", "refusal", "truncated"):
            with self.subTest(case=case):
                result = self.run_graph(MockSummaryClient(case))
                self.assertEqual(result["status"], "rejected")
                self.assertEqual(result["summary"], {})
                self.assertFalse(any("结构校验" in line for line in result["logs"]))

    def test_even_complete_json_is_rejected_if_marked_truncated(self):
        content = FIXTURES.joinpath("success.json").read_text(encoding="utf-8")
        result = self.run_graph(ResponseClient(content, {"finish_reason": "length"}))
        self.assertEqual(result["status"], "rejected")
        self.assertIn("截断", result["error"])

    def test_empty_and_oversize_response_are_rejected(self):
        for content in ("", " \n ", "x" * 8001):
            with self.subTest(length=len(content)):
                self.assertEqual(self.run_graph(ResponseClient(content))["status"], "rejected")

    def test_invalid_input_never_calls_model(self):
        cases = [("empty.txt", b" \n "), ("bad.txt", b"\xff"), ("huge.txt", b"x" * 65537),
                 ("long.txt", ("字" * 4001).encode()), ("wrong.md", b"text")]
        for name, data in cases:
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(data)
                client = ResponseClient("{}")
                result = self.run_graph(client, path)
                self.assertEqual((result["status"], client.calls), ("rejected", 0))
        client = ResponseClient("{}")
        self.assertEqual(self.run_graph(client, self.root / "missing.txt")["status"], "rejected")
        self.assertEqual(client.calls, 0)

    def test_bom_uppercase_extension_and_space_path(self):
        path = self.root / "中文 路径.TXT"
        path.write_text(FIXTURES.joinpath("travel_policy.txt").read_text(encoding="utf-8"), encoding="utf-8-sig")
        self.assertEqual(self.run_graph(path=path)["status"], "accepted")

    def test_mock_does_not_present_fixed_summary_for_other_content(self):
        path = self.root / "different.txt"
        path.write_text("另一份不相关的资料。", encoding="utf-8")
        result = self.run_graph(path=path)
        self.assertEqual(result["status"], "rejected")
        self.assertIn("固定响应仅适用于", result["error"])

    def test_messages_context_and_config_are_separate_from_state(self):
        client = ResponseClient(FIXTURES.joinpath("success.json").read_text(encoding="utf-8"))
        result = self.run_graph(client)
        self.assertEqual([message.type for message in client.messages], ["system", "human"])
        self.assertIn("JSON Schema", client.messages[0].content)
        self.assertEqual(client.messages[1].content, result["document"])
        self.assertIn("local-test", client.config["tags"])
        self.assertNotIn("client", result)
        self.assertNotIn("recursion_limit", result)

    def test_same_graph_can_succeed_after_previous_failure(self):
        self.run_graph(MockSummaryClient("missing-field"))
        result = self.run_graph()
        self.assertEqual((result["status"], result["error"], len(result["logs"])), ("accepted", "", 4))

    def test_input_is_not_modified(self):
        data = {"input_path": str(FIXTURES.joinpath("travel_policy.txt")), "logs": []}
        before = copy.deepcopy(data)
        self.graph.invoke(data, context=SummaryContext(MockSummaryClient()))
        self.assertEqual(data, before)

    def test_structural_success_does_not_validate_facts(self):
        result = self.run_graph(ResponseClient('{"summary":"火星差旅全额报销。","key_points":["没有审批要求。"]}'))
        self.assertEqual(result["status"], "accepted")
        # 这个反例明确校验边界，不将结构通过称为事实验证。


class TransportTests(unittest.TestCase):
    def invoke_with_transport(self, handler):
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            adapter = DeepSeekSummaryClient(Settings("local-test-key", "deepseek-flash"), http_client=http)
            return build_graph().invoke(
                {"input_path": str(FIXTURES.joinpath("travel_policy.txt")), "logs": []},
                context=SummaryContext(adapter), config={"recursion_limit": 16},
            )

    def test_actual_adapter_serializes_request_and_decodes_response(self):
        requests = []

        def handler(request):
            requests.append(request)
            body = json.loads(request.content)
            self.assertEqual(request.url.host, "api.deepseek.com")
            self.assertEqual(request.url.path, "/chat/completions")
            self.assertEqual(body["response_format"], {"type": "json_object"})
            self.assertEqual(body["thinking"], {"type": "disabled"})
            self.assertEqual(body["max_tokens"], 800)
            self.assertEqual([item["role"] for item in body["messages"]], ["system", "user"])
            content = FIXTURES.joinpath("success.json").read_text(encoding="utf-8")
            return httpx.Response(200, json={
                "id": "local-test", "object": "chat.completion", "created": 1, "model": body["model"],
                "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
            })
        result = self.invoke_with_transport(handler)
        self.assertEqual((result["status"], len(requests)), ("accepted", 1))
        self.assertNotIn("local-test-key", json.dumps(result, ensure_ascii=False))

    def test_http_errors_are_sanitized_and_not_retried(self):
        for status in (400, 401, 429, 500):
            calls = []

            def handler(request):
                calls.append(request)
                return httpx.Response(status, json={"error": {"message": "secret-from-server", "type": "test_error"}})
            with self.subTest(status=status):
                result = self.invoke_with_transport(handler)
                self.assertEqual((result["status"], len(calls)), ("rejected", 1))
                self.assertIn(f"HTTP {status}", result["error"])
                self.assertNotIn("secret-from-server", json.dumps(result))

    def test_http_timeout_is_not_retried(self):
        calls = []

        def handler(request):
            calls.append(request)
            raise httpx.ReadTimeout("sensitive request details", request=request)
        result = self.invoke_with_transport(handler)
        self.assertEqual((result["status"], len(calls)), ("rejected", 1))
        self.assertIn("超时", result["error"])


class ConfigurationAndCliTests(unittest.TestCase):
    def test_missing_credentials_and_model_are_explicit(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ConfigurationError):
            Settings.from_env()
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "local-key", "DEEPSEEK_MODEL": " "}, clear=True):
            with self.assertRaises(ConfigurationError):
                Settings.from_env()
        self.assertNotIn("local-key", repr(Settings("local-key", "model")))

    def test_cli_modes_errors_and_state_output(self):
        env = dict(os.environ, PYTHONUTF8="1")
        env.pop("DEEPSEEK_API_KEY", None)
        env.pop("DEEPSEEK_MODEL", None)
        cases = [([], 0), (["--mock-case", "missing-field"], 1), (["--mock-case", "invalid-json"], 1),
                 (["--mock-case", "timeout"], 1), (["--mode", "real"], 2),
                 (["--mode", "real", "--mock-case", "success"], 2), (["--show-state"], 0)]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, "-m", "chapter_demo", *arguments],
                                        env=env, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected == 0:
                    self.assertEqual(result.stderr, "")
                    self.assertIn("mock（固定响应，未调用模型）", result.stdout)
                else:
                    self.assertEqual(result.stdout, "")
                if "--show-state" in arguments:
                    self.assertIn("最终状态", result.stdout)
                    self.assertNotIn("api_key", result.stdout)


if __name__ == "__main__":
    unittest.main()
