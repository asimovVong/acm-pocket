"""Verify authored literal cases and starter I/O for the 20 backtracking/DP tasks.

Run with: python3 tests/verify_dp.py
The reference algorithms below are independent of the deliberately unfinished
starters. Small-case exhaustive searches are intentional; this is a catalog
sanity check, not a replacement for LeetCode's complete test suite.
Official problem links and input contracts are stored in data/dp.json.
"""

import ast
from collections import Counter, deque
from contextlib import redirect_stdout
from functools import lru_cache
from io import StringIO
from itertools import combinations, permutations, product
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
IDS = [
    "17", "78", "131", "77", "216", "22", "46", "51", "52", "198",
    "494", "322", "1143", "72", "300", "122", "309", "188", "516", "1039",
]


def all_subsequences(values):
    for size in range(len(values) + 1):
        yield from combinations(values, size)


def letters(digits):
    keys = dict(zip("23456789", ("abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz")))
    return ["".join(chars) for chars in product(*(keys[d] for d in digits))]


def partitions(s):
    answer = []
    # A bit after each character chooses whether to cut at that position.
    for cuts in range(1 << (len(s) - 1)):
        pieces = []
        start = 0
        for i in range(len(s) - 1):
            if cuts & (1 << i):
                pieces.append(s[start:i + 1])
                start = i + 1
        pieces.append(s[start:])
        if all(piece == piece[::-1] for piece in pieces):
            answer.append(pieces)
    return answer


def parentheses(n):
    answer = []
    for chars in product("()", repeat=2 * n):
        balance = 0
        for char in chars:
            balance += 1 if char == "(" else -1
            if balance < 0:
                break
        else:
            if balance == 0:
                answer.append("".join(chars))
    return answer


def queens(n):
    answer = []
    # A column permutation already places one queen in every row and column.
    for cols in permutations(range(n)):
        if len({r - c for r, c in enumerate(cols)}) != n:
            continue
        if len({r + c for r, c in enumerate(cols)}) != n:
            continue
        answer.append(["." * c + "Q" + "." * (n - c - 1) for c in cols])
    return answer


def robber(nums):
    answer = 0
    for mask in range(1 << len(nums)):
        if mask & (mask << 1):
            continue
        answer = max(answer, sum(x for i, x in enumerate(nums) if mask & (1 << i)))
    return answer


def target_sum(nums, target):
    return sum(
        sum(sign * num for sign, num in zip(signs, nums)) == target
        for signs in product((-1, 1), repeat=len(nums))
    )


def coin_change(coins, amount):
    # Each BFS edge adds one coin, so the first visit uses the fewest coins.
    queue = deque([(0, 0)])
    seen = {0}
    while queue:
        total, count = queue.popleft()
        if total == amount:
            return count
        for coin in coins:
            new_total = total + coin
            if new_total <= amount and new_total not in seen:
                seen.add(new_total)
                queue.append((new_total, count + 1))
    return -1


def lcs(text1, text2):
    left = set(all_subsequences(text1))
    right = set(all_subsequences(text2))
    return max(map(len, left & right))


def edit_distance(word1, word2):
    @lru_cache(None)
    def visit(i, j):
        if i == len(word1):
            return len(word2) - j
        if j == len(word2):
            return len(word1) - i
        if word1[i] == word2[j]:
            return visit(i + 1, j + 1)
        return 1 + min(visit(i + 1, j), visit(i, j + 1), visit(i + 1, j + 1))

    return visit(0, 0)


def lis(nums):
    return max(
        len(seq) for seq in all_subsequences(nums)
        if all(a < b for a, b in zip(seq, seq[1:]))
    )


def stock_profit(prices, max_trades=None, cooldown=0):
    if max_trades is None:
        max_trades = len(prices)

    @lru_cache(None)
    def visit(day, holding, remaining):
        if day >= len(prices):
            return -10**9 if holding else 0
        best = visit(day + 1, holding, remaining)
        if holding:
            best = max(best, prices[day] + visit(day + cooldown + 1, False, remaining - 1))
        elif remaining:
            best = max(best, -prices[day] + visit(day + 1, True, remaining))
        return best

    return visit(0, False, max_trades)


def longest_palindrome(s):
    return max(len(seq) for seq in all_subsequences(s) if seq == seq[::-1])


def triangulation(values):
    @lru_cache(None)
    def visit(left, right):
        if right - left < 2:
            return 0
        return min(
            values[left] * values[mid] * values[right]
            + visit(left, mid) + visit(mid, right)
            for mid in range(left + 1, right)
        )

    return visit(0, len(values) - 1)


REFERENCES = {
    "17": letters,
    "78": lambda nums: [list(seq) for seq in all_subsequences(nums)],
    "131": partitions,
    "77": lambda n, k: [list(seq) for seq in combinations(range(1, n + 1), k)],
    "216": lambda k, n: [list(seq) for seq in combinations(range(1, 10), k) if sum(seq) == n],
    "22": parentheses,
    "46": lambda nums: [list(seq) for seq in permutations(nums)],
    "51": queens,
    "52": lambda n: len(queens(n)),
    "198": robber,
    "494": target_sum,
    "322": coin_change,
    "1143": lcs,
    "72": edit_distance,
    "300": lis,
    "122": stock_profit,
    "309": lambda prices: stock_profit(prices, cooldown=1),
    "188": stock_profit,
    "516": longest_palindrome,
    "1039": triangulation,
}


def parse_arguments(identifier, stdin):
    lines = stdin.splitlines()
    if identifier in {"17", "131", "516"}:
        assert len(lines) == 1
        return (lines[0],)
    if identifier in {"1143", "72"}:
        assert len(lines) == 2, "Empty strings must retain their input lines"
        return tuple(lines)
    if identifier in {"22", "51", "52"}:
        return (int(stdin),)
    if identifier in {"77", "216"}:
        args = tuple(map(int, stdin.split()))
        assert len(args) == 2
        return args
    assert len(lines) == 2
    header = list(map(int, lines[0].split()))
    nums = list(map(int, lines[1].split()))
    assert len(nums) == header[0], "Array count does not match n"
    if identifier in {"494", "322", "188"}:
        assert len(header) == 2
        return nums, header[1]
    assert len(header) == 1
    return (nums,)


def normalized_json(value, judge):
    assert isinstance(value, list), "Collection output must be a JSON array"
    if judge == "unordered-nested":
        assert all(isinstance(item, list) for item in value)
        value = [sorted(item) for item in value]
    # Counter preserves duplicate multiplicity while ignoring only outer order.
    return Counter(json.dumps(item, ensure_ascii=False) for item in value)


def assert_output(actual, expected, judge, label):
    if judge == "tokens":
        assert actual.split() == expected.split(), f"{label}: {actual!r} != {expected!r}"
    else:
        actual_value, expected_value = json.loads(actual), json.loads(expected)
        assert normalized_json(actual_value, judge) == normalized_json(expected_value, judge), label


def check_starter(question, args, result, case):
    namespace = {"__name__": "starter_verification"}
    exec(compile(question["starter"], f"starter_{question['id']}.py", "exec"), namespace)
    calls = []

    def probe(*received):
        assert received == args, f"{question['id']}: starter parsed incorrect arguments"
        calls.append(received)
        return result

    namespace["solve"] = probe
    original_stdin = sys.stdin
    output = StringIO()
    try:
        sys.stdin = StringIO(case["stdin"])
        with redirect_stdout(output):
            namespace["main"]()
    finally:
        sys.stdin = original_stdin
    assert len(calls) == 1
    assert_output(output.getvalue(), case["expected"], question["judge"], f"starter {question['id']}")


def main():
    questions = json.loads((ROOT / "data/dp.json").read_text())
    sources = {q["id"]: q for q in json.loads((ROOT / "data/source-manifest.json").read_text())}
    assert [q["id"] for q in questions] == IDS
    required = {
        "id", "title", "topic", "episode", "episodes", "url", "statement",
        "inputFormat", "outputFormat", "starter", "judge", "cases",
    }
    checked = 0
    for question in questions:
        identifier = question["id"]
        assert set(question) == required
        for key in ("title", "episode", "url"):
            assert question[key] == sources[identifier][key], (identifier, key)
        assert question["episodes"] == [question["episode"]]
        expected_topic = "回溯" if question["episode"] <= 16 else "动态规划"
        assert question["topic"] == expected_topic
        expected_judge = (
            "unordered-nested" if identifier in {"78", "77", "216"}
            else "unordered" if identifier in {"17", "131", "22", "46", "51"}
            else "tokens"
        )
        assert question["judge"] == expected_judge
        assert all(question[field].strip() for field in ("statement", "inputFormat", "outputFormat"))
        assert len(question["cases"]) >= 3
        assert len({case["name"] for case in question["cases"]}) == len(question["cases"])
        tree = ast.parse(question["starter"])
        solve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "solve")
        assert len(solve.body) == 1 and isinstance(solve.body[0], ast.Raise), identifier
        for case in question["cases"]:
            assert set(case) == {"name", "stdin", "expected"}
            args = parse_arguments(identifier, case["stdin"])
            result = REFERENCES[identifier](*args)
            output = str(result) if question["judge"] == "tokens" else json.dumps(result, ensure_ascii=False)
            label = f"{identifier} / {case['name']}"
            assert_output(output, case["expected"], question["judge"], label)
            check_starter(question, args, result, case)
            checked += 1
    print(f"Verified {len(questions)} questions, {checked} literal cases, and {checked} starter I/O checks.")


if __name__ == "__main__":
    main()
