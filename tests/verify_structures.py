"""Verify fixed structures.json cases and every starter's input/output adapter.

Run: python3 tests/verify_structures.py
Uses only the standard library. The solutions below are verification references,
not learner starters. Expected answers are always read from the literal catalog.
Small exhaustive references deliberately check the tree optimization cases by
enumeration rather than deriving expected answers from the starter code.
"""

import ast
from collections import deque
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "data/structures.json").read_text())
IDS = "206 92 25 876 141 142 143 237 19 83 82 104 100 101 110 199 98 236 235 102 103 513 543 124 2246 337 968".split()
LINKED_IDS = set(IDS[:11])


class Node:
    def __init__(self, value):
        self.val = value
        self.next = None
        self.left = None
        self.right = None


def read_tree(line):
    """Independent tree decoder: consume pairs for successive non-null nodes."""
    values = iter(json.loads(line))
    first = next(values, None)
    if first is None:
        return None
    root = Node(first)
    pending = [root]
    for parent in pending:
        left, right = next(values, None), next(values, None)
        if left is not None:
            parent.left = Node(left)
            pending.append(parent.left)
        if right is not None:
            parent.right = Node(right)
            pending.append(parent.right)
    return root


def nodes_in_tree(root):
    if root is None:
        return []
    nodes = [root]
    for node in nodes:
        if node.left is not None:
            nodes.append(node.left)
        if node.right is not None:
            nodes.append(node.right)
    return nodes


def find_value(root, value):
    return next(node for node in nodes_in_tree(root) if node.val == value)


def chain_values(head):
    result, visited = [], set()
    while head is not None:
        if head in visited:
            raise AssertionError("A result intended to be acyclic contains a cycle")
        visited.add(head)
        result.append(head.val)
        head = head.next
    return result


def reverse_list(head):
    before = None
    while head is not None:
        after = head.next
        head.next = before
        before, head = head, after
    return before


def reverse_between(head, left, right):
    sentinel = Node(0)
    sentinel.next = head
    before = sentinel
    for _ in range(left - 1):
        before = before.next
    first = before.next
    for _ in range(right - left):
        moved = first.next
        first.next = moved.next
        moved.next = before.next
        before.next = moved
    return sentinel.next


def reverse_groups(head, k):
    sentinel = Node(0)
    sentinel.next = head
    before = sentinel
    while True:
        end = before
        for _ in range(k):
            end = end.next
            if end is None:
                return sentinel.next
        after = end.next
        node = before.next
        old_start = node
        previous = after
        while node is not after:
            following = node.next
            node.next = previous
            previous, node = node, following
        before.next = end
        before = old_start


def middle_node(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
    return slow


def cycle_entry(head):
    seen = set()
    while head is not None:
        if head in seen:
            return head
        seen.add(head)
        head = head.next
    return None


def has_cycle(head):
    return cycle_entry(head) is not None


def reorder_list(head):
    nodes = []
    node = head
    while node is not None:
        nodes.append(node)
        node = node.next
    order = []
    left, right = 0, len(nodes) - 1
    while left <= right:
        order.append(nodes[left])
        if left != right:
            order.append(nodes[right])
        left += 1
        right -= 1
    for index, node in enumerate(order):
        node.next = order[index + 1] if index + 1 < len(order) else None


def delete_given_node(node):
    node.val = node.next.val
    node.next = node.next.next


def remove_from_end(head, k):
    sentinel = Node(0)
    sentinel.next = head
    lead = sentinel
    for _ in range(k):
        lead = lead.next
    before = sentinel
    while lead.next is not None:
        lead, before = lead.next, before.next
    before.next = before.next.next
    return sentinel.next


def keep_one_duplicate(head):
    node = head
    while node is not None and node.next is not None:
        if node.val == node.next.val:
            node.next = node.next.next
        else:
            node = node.next
    return head


def keep_only_unique(head):
    sentinel = Node(0)
    sentinel.next = head
    before = sentinel
    while head is not None:
        end = head
        while end.next is not None and end.next.val == head.val:
            end = end.next
        if end is head:
            before = head
        else:
            before.next = end.next
        head = end.next
    return sentinel.next


def levels(root):
    current = [] if root is None else [root]
    result = []
    while current:
        result.append([node.val for node in current])
        current = [child for node in current for child in (node.left, node.right) if child is not None]
    return result


def max_depth(root):
    return len(levels(root))


def same_tree(a, b):
    if a is None or b is None:
        return a is b
    return a.val == b.val and same_tree(a.left, b.left) and same_tree(a.right, b.right)


def symmetric(root):
    def mirrors(left, right):
        if left is None or right is None:
            return left is right
        return left.val == right.val and mirrors(left.left, right.right) and mirrors(left.right, right.left)
    return root is None or mirrors(root.left, root.right)


def balanced(root):
    return all(abs(max_depth(node.left) - max_depth(node.right)) <= 1 for node in nodes_in_tree(root))


def right_view(root):
    return [level[-1] for level in levels(root)]


def valid_bst(root):
    def visit(node, lower, upper):
        if node is None:
            return True
        return lower < node.val < upper and visit(node.left, lower, node.val) and visit(node.right, node.val, upper)
    return visit(root, float("-inf"), float("inf"))


def lowest_common_ancestor(root, p, q):
    parents = {root: None}
    for node in nodes_in_tree(root):
        for child in (node.left, node.right):
            if child is not None:
                parents[child] = node
    ancestors = set()
    while p is not None:
        ancestors.add(p)
        p = parents[p]
    while q not in ancestors:
        q = parents[q]
    return q


def zigzag(root):
    return [row if index % 2 == 0 else row[::-1] for index, row in enumerate(levels(root))]


def bottom_left(root):
    return levels(root)[-1][0]


def tree_graph(root):
    nodes = nodes_in_tree(root)
    adjacency = {node: [] for node in nodes}
    for node in nodes:
        for child in (node.left, node.right):
            if child is not None:
                adjacency[node].append(child)
                adjacency[child].append(node)
    return nodes, adjacency


def diameter(root):
    nodes, adjacency = tree_graph(root)
    answer = 0
    for start in nodes:
        stack = [(start, None, 0)]
        while stack:
            node, previous, distance = stack.pop()
            answer = max(answer, distance)
            stack.extend((child, node, distance + 1) for child in adjacency[node] if child is not previous)
    return answer


def maximum_path_sum(root):
    nodes, adjacency = tree_graph(root)
    answer = float("-inf")
    for start in nodes:
        stack = [(start, None, start.val)]
        while stack:
            node, previous, total = stack.pop()
            answer = max(answer, total)
            stack.extend((child, node, total + child.val) for child in adjacency[node] if child is not previous)
    return answer


def longest_different_path(parent, s):
    adjacency = [[] for _ in parent]
    for node in range(1, len(parent)):
        ancestor = parent[node]
        adjacency[node].append(ancestor)
        adjacency[ancestor].append(node)
    answer = 1
    for start in range(len(parent)):
        stack = [(start, -1, 1)]
        while stack:
            node, previous, size = stack.pop()
            answer = max(answer, size)
            stack.extend((child, node, size + 1) for child in adjacency[node] if child != previous and s[child] != s[node])
    return answer


def rob_tree(root):
    nodes, adjacency = tree_graph(root)
    answer = 0
    for mask in range(1 << len(nodes)):
        selected = {node for index, node in enumerate(nodes) if mask & (1 << index)}
        if all(not any(child in selected for child in adjacency[node]) for node in selected):
            answer = max(answer, sum(node.val for node in selected))
    return answer


def minimum_cameras(root):
    nodes, adjacency = tree_graph(root)
    answer = len(nodes)
    for mask in range(1 << len(nodes)):
        cameras = {node for index, node in enumerate(nodes) if mask & (1 << index)}
        if len(cameras) >= answer:
            continue
        covered = cameras.copy()
        for node in cameras:
            covered.update(adjacency[node])
        if len(covered) == len(nodes):
            answer = len(cameras)
    return answer


REFERENCES = dict(zip(IDS, [
    reverse_list, reverse_between, reverse_groups, middle_node, has_cycle,
    cycle_entry, reorder_list, delete_given_node, remove_from_end,
    keep_one_duplicate, keep_only_unique, max_depth, same_tree, symmetric,
    balanced, right_view, valid_bst, lowest_common_ancestor,
    lowest_common_ancestor, levels, zigzag, bottom_left, diameter,
    maximum_path_sum, longest_different_path, rob_tree, minimum_cameras,
]))


def independent_result(problem_id, stdin):
    """Decode cases independently of starter helpers and serialize the result."""
    lines = stdin.splitlines()
    reference = REFERENCES[problem_id]
    if problem_id in LINKED_IDS:
        header = list(map(int, lines[0].split()))
        values = list(map(int, lines[1].split())) if len(lines) > 1 else []
        assert header[0] == len(values)
        nodes = [Node(value) for value in values]
        for index in range(1, len(nodes)):
            nodes[index - 1].next = nodes[index]
        head = nodes[0] if nodes else None
        if problem_id in {"141", "142"}:
            position = header[1]
            if position >= 0:
                nodes[-1].next = nodes[position]
            answer = reference(head)
            if problem_id == "141":
                return int(answer)
            return -1 if answer is None else nodes.index(answer)
        if problem_id == "237":
            reference(nodes[header[1]])
            return chain_values(head)
        if problem_id == "143":
            reference(head)
            return chain_values(head)
        return chain_values(reference(head, *header[1:]))
    if problem_id == "2246":
        n = int(lines[0])
        parent, s = list(map(int, lines[1].split())), lines[2]
        assert len(parent) == len(s) == n
        return reference(parent, s)
    root = read_tree(lines[0])
    if problem_id == "100":
        return int(reference(root, read_tree(lines[1])))
    if problem_id in {"235", "236"}:
        p, q = map(int, lines[1].split())
        return reference(root, find_value(root, p), find_value(root, q)).val
    answer = reference(root)
    return int(answer) if isinstance(answer, bool) else answer


class StructureCatalogTests(unittest.TestCase):
    def assert_output(self, record, actual, expected):
        if record["judge"] == "json":
            self.assertEqual(json.loads(actual), json.loads(expected))
        else:
            self.assertEqual(actual.split(), expected.split())

    def test_catalog_contract_and_starter_syntax(self):
        manifest = {p["id"]: p for p in json.loads((ROOT / "data/source-manifest.json").read_text())}
        self.assertEqual([record["id"] for record in CATALOG], IDS)
        required = {"id", "title", "topic", "episode", "episodes", "url", "statement", "inputFormat", "outputFormat", "starter", "judge", "cases"}
        for record in CATALOG:
            with self.subTest(problem=record["id"]):
                self.assertTrue(required.issubset(record))
                self.assertGreaterEqual(len(record["cases"]), 3)
                self.assertEqual(len({case["name"] for case in record["cases"]}), len(record["cases"]))
                self.assertIn(record["judge"], {"json", "tokens"})
                for key in ("title", "url", "episode"):
                    self.assertEqual(record[key], manifest[record["id"]][key])
                compile(record["starter"], record["id"] + "_starter.py", "exec")
                tree = ast.parse(record["starter"])
                solve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "solve")
                self.assertEqual(len(solve.body), 1)
                self.assertIsInstance(solve.body[0], ast.Raise)
                self.assertEqual(solve.body[0].exc.func.id, "NotImplementedError")
                if record["id"] == "237":
                    self.assertEqual([arg.arg for arg in solve.args.args], ["node"])
                if record["id"] in {"141", "142"}:
                    self.assertEqual([arg.arg for arg in solve.args.args], ["head"])

    def test_fixed_answers_against_independent_references(self):
        for record in CATALOG:
            for case in record["cases"]:
                with self.subTest(problem=record["id"], case=case["name"]):
                    result = independent_result(record["id"], case["stdin"])
                    self.assert_output(record, json.dumps(result), case["expected"])

    def test_starter_adapters_with_reference_injection(self):
        for record in CATALOG:
            for case in record["cases"]:
                with self.subTest(problem=record["id"], case=case["name"]):
                    namespace = {"__name__": "catalog_test"}
                    exec(compile(record["starter"], record["id"] + "_starter.py", "exec"), namespace)
                    # First show that the untouched template reads valid input and
                    # reaches the deliberately unimplemented learner function.
                    with patch("sys.stdin", io.StringIO(case["stdin"])):
                        with self.assertRaises(NotImplementedError):
                            namespace["main"]()
                    # Then supply only the independent solution, preserving the
                    # starter's real classes, parsing, function call and output.
                    reference = REFERENCES[record["id"]]

                    def checked_reference(*args, _reference=reference, _id=record["id"]):
                        if _id in LINKED_IDS and args[0] is not None:
                            self.assertIsInstance(args[0], namespace["ListNode"])
                        if _id == "237":
                            self.assertEqual(len(args), 1)
                            self.assertIsNotNone(args[0].next)
                        if _id in {"141", "142"}:
                            self.assertEqual(len(args), 1)
                            entry = cycle_entry(args[0])
                            self.assertEqual(entry is not None, int(case["stdin"].splitlines()[0].split()[1]) >= 0)
                        if _id not in LINKED_IDS and _id != "2246":
                            for node in args:
                                if node is not None:
                                    self.assertIsInstance(node, namespace["TreeNode"])
                        return _reference(*args)

                    namespace["solve"] = checked_reference
                    output = io.StringIO()
                    with patch("sys.stdin", io.StringIO(case["stdin"])), redirect_stdout(output):
                        namespace["main"]()
                    self.assert_output(record, output.getvalue(), case["expected"])


if __name__ == "__main__":
    print(f"Verifying {len(CATALOG)} structure problems / {sum(len(p['cases']) for p in CATALOG)} literal cases", flush=True)
    unittest.main(verbosity=2)
