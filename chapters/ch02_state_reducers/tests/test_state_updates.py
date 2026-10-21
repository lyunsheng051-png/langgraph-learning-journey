"""验证真实图执行中的更新语义，不调用模型或网络。"""

from copy import deepcopy
from pathlib import Path
from tempfile import gettempdir, TemporaryDirectory
import unittest
from unittest.mock import patch

from chapter_demo import graph as graph_module


class StateUpdatesTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="langgraph-ch02-")
        root = Path(self.directory.name).resolve()
        self.assertEqual(root.parent, Path(gettempdir()).resolve())
        self.addCleanup(self.directory.cleanup)
        self.path = root / "样例.txt"
        self.path.write_text("甲乙。\n\n丙。", encoding="utf-8", newline="\n")
        self.initial = {"input_path": str(self.path), "logs": []}
        self.expected_logs = ["已读取：样例.txt", "已统计：5 个非空白字符，2 个段落", "已整理统计报告"]

    def test_without_reducer_only_the_last_log_remains(self):
        result = graph_module.build_graph("overwrite").invoke(self.initial)
        self.assertEqual(result["logs"], self.expected_logs[-1:])
        self.assertEqual(result["character_count"], 5)
        self.assertEqual(result["step"], "整理完成")

    def test_reducer_accumulates_only_new_entries(self):
        result = graph_module.build_graph("append").invoke(self.initial)
        self.assertEqual(result["logs"], self.expected_logs)
        self.assertEqual(result["step"], "整理完成")
        self.assertEqual(self.initial["logs"], [])

    def test_partial_updates_keep_fields_for_later_nodes(self):
        observed = {}
        original = graph_module.format_report

        def inspect_report_input(state):
            observed.update(deepcopy(state))
            return original(state)

        with patch.object(graph_module, "format_report", inspect_report_input):
            result = graph_module.build_graph().invoke(self.initial)
        self.assertEqual(observed["input_path"], str(self.path))
        self.assertEqual(observed["text"], "甲乙。\n\n丙。")
        self.assertEqual(observed["logs"], self.expected_logs[:2])
        self.assertEqual(observed["step"], "统计完成")
        self.assertNotIn("report", observed)
        self.assertEqual(result["input_path"], str(self.path))
        self.assertIn("report", result)

    def test_returning_full_history_causes_duplicate_entries(self):
        original = graph_module.analyze_document

        def return_full_history(state):
            update = original(state)
            update["logs"] = state["logs"] + update["logs"]
            return update

        with patch.object(graph_module, "analyze_document", return_full_history):
            result = graph_module.build_graph().invoke(self.initial)
        self.assertEqual(result["logs"], [self.expected_logs[0], *self.expected_logs])

    def test_separate_invocations_do_not_share_log_history(self):
        graph = graph_module.build_graph()
        first = graph.invoke(self.initial)
        second = graph.invoke({"input_path": str(self.path), "logs": []})
        self.assertEqual(first["logs"], self.expected_logs)
        self.assertEqual(second["logs"], self.expected_logs)


if __name__ == "__main__":
    unittest.main()
