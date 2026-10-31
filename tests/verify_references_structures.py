"""Run shipped structures references against fixtures and node identity checks.

Run: python3 tests/verify_references_structures.py
Fixture expectations come from structures.json; judge.mjs compares actual output.
"""

import ast
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / 'data/structures.json').read_text())
REFERENCES = json.loads((ROOT / 'data/references-structures.json').read_text())
BY_ID = {reference['id']: reference for reference in REFERENCES}


def namespace(question_id):
    scope = {'__name__': 'reference_under_test'}
    exec(compile(BY_ID[question_id]['code'], f'reference-{question_id}.py', 'exec'), scope)
    return scope


def ordered_nodes(head):
    nodes = []
    while head is not None:
        assert head not in nodes, 'Unexpected cycle in a result list'
        nodes.append(head)
        head = head.next
    return nodes


def verify_fixtures():
    assert len(REFERENCES) == len(QUESTIONS) == len(BY_ID)
    results = []
    for question in QUESTIONS:
        reference = BY_ID[question['id']]
        code = reference['code']
        parsed = ast.parse(code)
        assert 'TODO' not in code and 'NotImplementedError' not in code
        actual_imports = {ast.unparse(node) for node in ast.walk(parsed)
                          if isinstance(node, (ast.Import, ast.ImportFrom))}
        assert actual_imports == {item['code'] for item in reference['imports']}
        assert reference['author'] == '灵茶山艾府'
        for case in question['cases']:
            run = subprocess.run([sys.executable, '-c', code], input=case['stdin'],
                                 text=True, capture_output=True, timeout=10)
            assert run.returncode == 0, (question['id'], case['name'], run.stderr)
            results.append({'id': question['id'], 'case': case['name'],
                            'actual': run.stdout, 'expected': case['expected'],
                            'rule': question['judge'], 'stdin': case['stdin']})
    compare_script = """
import fs from 'node:fs';
import { compareOutput } from './judge.mjs';
const results = JSON.parse(fs.readFileSync(0, 'utf8'));
const failures = results.filter(row => !compareOutput(row.actual, row.expected, row.rule, row.stdin).pass);
if (failures.length) { console.error(JSON.stringify(failures, null, 2)); process.exit(1); }
console.log(`structures references: ${results.length}/${results.length} fixtures passed`);
"""
    compared = subprocess.run(['node', '--input-type=module', '-e', compare_script],
                              input=json.dumps(results), text=True, capture_output=True,
                              cwd=ROOT, timeout=10)
    assert compared.returncode == 0, compared.stderr
    print(compared.stdout.strip())


def verify_node_identity():
    # Expected node orders are literal; equal values cannot disguise copied nodes.
    for question_id, values, args, expected_indexes in [
        ('206', [1, 2, 3, 4, 5], (), [4, 3, 2, 1, 0]),
        ('92', [1, 2, 3, 4, 5], (2, 4), [0, 3, 2, 1, 4]),
        ('25', [1, 2, 3, 4, 5], (2,), [1, 0, 3, 2, 4]),
        ('19', [1, 2, 3, 4, 5], (2,), [0, 1, 2, 4]),
        ('83', [1, 1, 2, 3, 3], (), [0, 2, 3]),
        ('82', [1, 1, 2, 3, 3, 4], (), [2, 5]),
    ]:
        scope = namespace(question_id)
        head, nodes = scope['build_list'](values)
        answer = scope['solve'](head, *args)
        assert ordered_nodes(answer) == [nodes[index] for index in expected_indexes], question_id

    scope = namespace('876')
    head, nodes = scope['build_list']([4, 4, 4, 4, 4, 4])
    assert scope['solve'](head) is nodes[3]

    for question_id in ['141', '142']:
        scope = namespace(question_id)
        head, nodes = scope['build_list']([7, 7, 7, 7])
        nodes[-1].next = nodes[1]
        links_before = [node.next for node in nodes]
        answer = scope['solve'](head)
        assert answer is (True if question_id == '141' else nodes[1])
        assert [node.next for node in nodes] == links_before

    scope = namespace('143')
    head, nodes = scope['build_list']([1, 2, 3, 4, 5])
    assert scope['solve'](head) is None
    assert ordered_nodes(head) == [nodes[0], nodes[4], nodes[1], nodes[3], nodes[2]]

    scope = namespace('237')
    head, nodes = scope['build_list']([4, 5, 1, 9])
    assert scope['solve'](nodes[1]) is None
    assert ordered_nodes(head) == [nodes[0], nodes[1], nodes[3]]
    assert [node.val for node in ordered_nodes(head)] == [4, 1, 9]

    for question_id in ['235', '236']:
        scope = namespace(question_id)
        root = scope['build_tree']([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5])
        assert scope['solve'](root, root.left.left, root.left.right.right) is root.left
    print('structures references: linked list and LCA node identity checks passed')


def verify_deep_general_tree():
    # A 100000-node chain whose parent indexes are not in topological order.
    # 0 -> n-1 -> n-2 -> ... -> 1, with alternating characters along the chain.
    n = 100_000
    parent = [-1] + list(range(2, n)) + [0]
    labels = ['a'] * n
    for depth, node in enumerate(range(n - 1, 0, -1), 1):
        labels[node] = 'b' if depth % 2 else 'a'
    assert namespace('2246')['solve'](parent, ''.join(labels)) == n
    print('structures references: 100000-node general-tree chain passed')


if __name__ == '__main__':
    verify_fixtures()
    verify_node_identity()
    verify_deep_general_tree()
