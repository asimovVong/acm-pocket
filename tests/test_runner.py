import unittest

try:
    from runner import execute_code
except ImportError:
    execute_code = None


class RunnerTests(unittest.TestCase):
    def run_code(self, code, stdin=""):
        self.assertTrue(callable(execute_code), "Python execution adapter is missing")
        return execute_code(code, stdin)

    def test_acm_input_and_print(self):
        result = self.run_code("n, target = map(int, input().split())\nnums = list(map(int, input().split()))\nprint(n, target, sum(nums))", "6 7\n2 3 1 2 4 3\n")
        self.assertEqual(result, {"stdout": "6 7 15\n", "stderr": "", "error": None})

    def test_binary_standard_streams_and_unicode(self):
        result = self.run_code("import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())", "你好\n42")
        self.assertEqual(result["stdout"], "你好\n42")

    def test_error_keeps_partial_output_and_source_line(self):
        result = self.run_code("print('before')\nprint(1/0)")
        self.assertEqual(result["stdout"], "before\n")
        self.assertIn("ZeroDivisionError", result["error"])
        self.assertIn("main.py", result["error"])
        self.assertIn("line 2", result["error"])

    def test_syntax_error_and_missing_input(self):
        self.assertIn("SyntaxError", self.run_code("if:")["error"])
        self.assertIn("EOFError", self.run_code("input()")["error"])

    def test_stderr_is_separate(self):
        result = self.run_code("import sys\nprint('debug', file=sys.stderr)\nprint(2)")
        self.assertEqual(result["stdout"], "2\n")
        self.assertEqual(result["stderr"], "debug\n")
        self.assertIsNone(result["error"])

    def test_successful_exit_does_not_stop_runner(self):
        result = self.run_code("import sys\nprint(1)\nsys.exit(0)\nprint(2)")
        self.assertEqual(result["stdout"], "1\n")
        self.assertIsNone(result["error"])
        self.assertIn("SystemExit", self.run_code("raise SystemExit(2)")["error"])

    def test_run_globals_are_fresh(self):
        self.run_code("private_value = 42")
        self.assertIn("NameError", self.run_code("print(private_value)")["error"])
        self.assertEqual(self.run_code("print(__name__)")["stdout"], "__main__\n")

    def test_large_output_is_bounded(self):
        result = self.run_code("print('x' * 100000)")
        self.assertIsNotNone(result["error"])
        self.assertLessEqual(len(result["stdout"].encode()), 65536)

    def test_larger_budget_allows_valid_combination_answers(self):
        self.assertTrue(callable(execute_code))
        result = execute_code("import json,itertools\nprint(json.dumps(list(itertools.combinations(range(1,17),8))))", "", output_limit=8 * 1024 * 1024)
        self.assertIsNone(result["error"])
        import json
        combinations = json.loads(result["stdout"])
        self.assertEqual(len(combinations), 12870)
        self.assertEqual(combinations[0], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(combinations[-1], [9, 10, 11, 12, 13, 14, 15, 16])


if __name__ == "__main__":
    unittest.main()
