"""Independently verify the array catalog's fixed fixtures; no third-party packages."""

import ast
from contextlib import redirect_stdout
import io
import itertools
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
IDS = ["167", "15", "11", "42", "209", "3", "713", "34", "162", "153", "33", "739", "239"]
TOPICS = {"双指针", "滑动窗口", "二分查找", "单调栈", "单调队列"}
FIELDS = {"id", "title", "topic", "episode", "episodes", "url", "statement", "inputFormat", "outputFormat", "starter", "judge", "cases"}
LEGACY_209 = [
    ("样例 1 · 常规窗口", "6 7\n2 3 1 2 4 3\n", "2"),
    ("样例 2 · 单个元素达标", "3 4\n1 4 4\n", "1"),
    ("样例 3 · 不存在答案", "8 11\n1 1 1 1 1 1 1 1\n", "0"),
    ("边界 1 · 数组只有一个元素", "1 7\n7\n", "1"),
    ("边界 2 · 必须使用整个数组", "5 15\n1 2 3 4 5\n", "5"),
    ("边界 3 · 需要多次收缩窗口", "6 11\n1 2 3 4 5 6\n", "2"),
]


def parse_array(problem_id, stdin):
    lines = stdin.splitlines()
    assert len(lines) == 2, (problem_id, "array input must contain exactly two lines")
    header = list(map(int, lines[0].split()))
    has_parameter = problem_id in {"167", "209", "713", "34", "33", "239"}
    assert len(header) == (2 if has_parameter else 1)
    nums = list(map(int, lines[1].split()))
    assert len(nums) == header[0], (problem_id, "n does not match array length")
    return nums, header[1] if has_parameter else None


def valid_peaks(nums):
    return [i for i, value in enumerate(nums)
            if (i == 0 or value > nums[i - 1])
            and (i == len(nums) - 1 or value > nums[i + 1])]


def reference(problem_id, stdin):
    """Small exhaustive or direct definitions, independent of the learner templates."""
    if problem_id == "3":
        text = stdin.rstrip("\r\n")
        assert "\n" not in text and "\r" not in text
        return max((end - start for start in range(len(text))
                    for end in range(start + 1, len(text) + 1)
                    if len(set(text[start:end])) == end - start), default=0)

    nums, parameter = parse_array(problem_id, stdin)
    n = len(nums)
    assert n >= (0 if problem_id == "34" else 1)
    if problem_id in {"167", "34"}:
        assert nums == sorted(nums)
    if problem_id in {"11", "42"}:
        assert all(value >= 0 for value in nums)
    if problem_id in {"209", "713"}:
        assert all(value > 0 for value in nums)
    if problem_id in {"153", "33"}:
        assert len(set(nums)) == n
        ordered = sorted(nums)
        assert any(nums == ordered[k:] + ordered[:k] for k in range(n))

    if problem_id == "167":
        assert n >= 2
        answers = [[i + 1, j + 1] for i, j in itertools.combinations(range(n), 2)
                   if nums[i] + nums[j] == parameter]
        assert len(answers) == 1, "167 requires a unique pair of indices"
        return answers[0]
    if problem_id == "15":
        assert n >= 3
        return sorted({tuple(sorted(triple)) for triple in itertools.combinations(nums, 3)
                       if sum(triple) == 0})
    if problem_id == "11":
        assert n >= 2
        return max((j - i) * min(nums[i], nums[j])
                   for i, j in itertools.combinations(range(n), 2))
    if problem_id == "42":
        return sum(max(0, min(max(nums[:i + 1]), max(nums[i:])) - value)
                   for i, value in enumerate(nums))
    if problem_id == "209":
        assert parameter > 0
        return min((end - start for start in range(n)
                    for end in range(start + 1, n + 1)
                    if sum(nums[start:end]) >= parameter), default=0)
    if problem_id == "713":
        assert parameter >= 0
        count = 0
        for start in range(n):
            for end in range(start + 1, n + 1):
                product = 1
                for value in nums[start:end]:
                    product *= value
                count += product < parameter
        return count
    if problem_id == "34":
        indices = [i for i, value in enumerate(nums) if value == parameter]
        return [indices[0], indices[-1]] if indices else [-1, -1]
    if problem_id == "162":
        assert all(a != b for a, b in zip(nums, nums[1:]))
        return valid_peaks(nums)
    if problem_id == "153":
        return min(nums)
    if problem_id == "33":
        return next((i for i, value in enumerate(nums) if value == parameter), -1)
    if problem_id == "739":
        assert all(30 <= value <= 100 for value in nums)
        return [next((j - i for j in range(i + 1, n) if nums[j] > value), 0)
                for i, value in enumerate(nums)]
    if problem_id == "239":
        assert 1 <= parameter <= n
        return [max(nums[i:i + parameter]) for i in range(n - parameter + 1)]
    raise AssertionError(f"Missing verifier for {problem_id}")


def smoke_starter(problem, stdin):
    """Exercise input helpers, with no claim that unfinished algorithms should pass."""
    original_stdin = sys.stdin
    stream = io.TextIOWrapper(io.BytesIO(stdin.encode("utf-8")), encoding="utf-8")
    try:
        sys.stdin = stream
        with redirect_stdout(io.StringIO()) as output:
            exec(compile(problem["starter"], f"starter-{problem['id']}.py", "exec"),
                 {"__name__": "__main__"})
        assert output.getvalue().strip(), "starter must include a usable output statement"
    finally:
        sys.stdin = original_stdin
        stream.close()


def main():
    problems = json.loads((ROOT / "data/arrays.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/source-manifest.json").read_text(encoding="utf-8"))
    assert [problem["id"] for problem in problems] == IDS
    total = 0
    for problem in problems:
        problem_id = problem["id"]
        assert set(problem) == FIELDS, problem_id
        sources = [entry for entry in manifest if entry["id"] == problem_id]
        assert problem["title"] == sources[0]["title"]
        assert problem["url"] == sources[0]["url"]
        assert problem["episode"] == sources[0]["episode"]
        assert problem["episodes"] == [entry["episode"] for entry in sources]
        assert problem["topic"] in TOPICS
        for field in ["statement", "inputFormat", "outputFormat", "starter"]:
            assert isinstance(problem[field], str) and problem[field].strip()
        assert len(problem["cases"]) >= 3
        assert len({case["name"] for case in problem["cases"]}) == len(problem["cases"])
        ast.parse(problem["starter"])
        expected_judge = ("peak" if problem_id == "162" else "unordered-nested" if problem_id == "15"
                          else "json" if problem_id in {"167", "34", "739", "239"} else "tokens")
        assert problem["judge"] == expected_judge
        if problem_id == "209":
            assert [(case["name"], case["stdin"], case["expected"]) for case in problem["cases"]] == LEGACY_209
        for case in problem["cases"]:
            assert set(case) == {"name", "stdin", "expected"}
            assert all(isinstance(value, str) for value in case.values())
            result = reference(problem_id, case["stdin"])
            expected = json.loads(case["expected"])
            if problem_id == "162":
                assert type(expected) is int and expected in result, (problem_id, case["name"], result, expected)
            else:
                if problem_id == "15":
                    assert isinstance(expected, list)
                    assert all(isinstance(row, list) and len(row) == 3 for row in expected)
                    expected = sorted(tuple(sorted(row)) for row in expected)
                assert result == expected, (problem_id, case["name"], result, expected)
            smoke_starter(problem, case["stdin"])
            total += 1
    print(f"PASS: {len(problems)} array/string/search/monotonic problems; {total} independently verified fixtures; all starters parse and run.")


if __name__ == "__main__":
    main()
