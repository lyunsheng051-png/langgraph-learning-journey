import copy
import os
import subprocess
import sys
import unittest
from importlib.resources import files

from langgraph.errors import GraphRecursionError

from chapter_demo.graph import build_graph
from chapter_demo.nodes import MISSING_SOURCE, MISSING_TITLE


def inputs(sample="draft", budget=2, mode="fix"):
    draft = files("chapter_demo").joinpath("fixtures", f"{sample}.md").read_text(encoding="utf-8")
    return {"draft": draft, "max_repairs": budget, "repair_mode": mode, "logs": []}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_graph()

    def run_graph(self, data):
        return self.graph.invoke(data, config={"recursion_limit": 32})

    def test_success_on_last_allowed_repair(self):
        result = self.run_graph(inputs())
        self.assertEqual((result["status"], result["repairs"], result["checks"]), ("accepted", 2, 3))
        self.assertEqual(result["issues"], [])
        self.assertIn("来源：travel_policy.txt", result["draft"])

    def test_complete_draft_does_not_need_a_repair(self):
        result = self.run_graph(inputs("complete", budget=0))
        self.assertEqual((result["status"], result["repairs"], result["checks"]), ("accepted", 0, 1))

    def test_one_repair_leaves_an_explicit_problem(self):
        result = self.run_graph(inputs(budget=1))
        self.assertEqual((result["status"], result["repairs"], result["checks"]), ("exhausted", 1, 2))
        self.assertEqual(result["issues"], [MISSING_SOURCE])
        self.assertTrue(result["draft"].startswith("# 出差资料整理"))

    def test_zero_budget_still_checks_initial_draft(self):
        original = inputs(budget=0)
        result = self.run_graph(original)
        self.assertEqual((result["status"], result["repairs"], result["checks"]), ("exhausted", 0, 1))
        self.assertEqual(result["issues"], [MISSING_TITLE, MISSING_SOURCE])
        self.assertEqual(result["draft"], original["draft"])

    def test_ineffective_repairs_stop_at_business_budget(self):
        result = self.run_graph(inputs(mode="unchanged"))
        self.assertEqual((result["status"], result["repairs"], result["checks"]), ("exhausted", 2, 3))
        self.assertEqual(result["issues"], [MISSING_TITLE, MISSING_SOURCE])

    def test_largest_budget_fits_normal_graph_limit(self):
        result = self.run_graph(inputs(budget=10, mode="unchanged"))
        self.assertEqual((result["status"], result["repairs"], result["checks"]), ("exhausted", 10, 11))

    def test_logs_preserve_sequence_without_copying_history(self):
        result = self.run_graph(inputs())
        self.assertEqual(result["logs"], [
            "开始：最多修正 2 次", "第 1 次检查：缺少标题、缺少来源行",
            "第 1 次修正：补上标题", "第 2 次检查：缺少来源行",
            "第 2 次修正：补上来源行", "第 3 次检查：通过", "结束：报告通过检查",
        ])

    def test_small_graph_limit_interrupts_even_bounded_workflow(self):
        with self.assertRaises(GraphRecursionError):
            self.graph.invoke(inputs(), config={"recursion_limit": 3})

    def test_same_graph_new_call_does_not_inherit_old_result(self):
        self.run_graph(inputs(budget=0))
        result = self.run_graph(inputs("complete"))
        self.assertEqual((result["status"], result["checks"], len(result["logs"])), ("accepted", 1, 3))
        self.assertEqual(result["issues"], [])

    def test_invalid_business_parameters_are_rejected(self):
        for budget in (-1, 11, True, 1.5):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                self.run_graph(inputs(budget=budget))
        with self.assertRaises(ValueError):
            self.run_graph(inputs(mode="unknown"))

    def test_input_is_not_modified(self):
        data = inputs()
        snapshot = copy.deepcopy(data)
        self.run_graph(data)
        self.assertEqual(data, snapshot)

    def test_cli_exit_codes_and_output_channels(self):
        env = dict(os.environ, PYTHONUTF8="1")
        cases = [([], 0), (["--max-repairs", "1"], 1),
                 (["--repair-mode", "unchanged"], 1),
                 (["--recursion-limit", "3"], 3),
                 (["--max-repairs", "-1"], 2), (["--max-repairs", "11"], 2),
                 (["--recursion-limit", "0"], 2)]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, "-m", "chapter_demo", *arguments],
                                        capture_output=True, text=True, encoding="utf-8", env=env)
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected == 0:
                    self.assertEqual(result.stderr, "")
                    self.assertIn("状态：通过", result.stdout)
                else:
                    self.assertEqual(result.stdout, "")
                    self.assertTrue(result.stderr)
                    self.assertNotIn("最终状态：", result.stderr)


if __name__ == "__main__":
    unittest.main()
