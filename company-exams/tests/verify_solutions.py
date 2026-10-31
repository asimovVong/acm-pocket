"""Independent small-input oracles plus original samples and maximum sizes."""
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / 'companies/didi/2026-09-06'


def load(relative):
    path = SESSION / relative / 'solution.py'
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(relative, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shelf = load('01-层板限差')
pipe = load('02-管材四切')


def brute_shelf(values, d):
    # Permute identities, so equal heights remain distinguishable.
    return sum(all(values[p[k + 1]] >= values[p[k]] - d
                   for k in range(len(p) - 1))
               for p in itertools.permutations(range(len(values))))


def brute_pipe(values):
    best = float('inf')
    for i, j, k in itertools.combinations(range(1, len(values)), 3):
        sums = [sum(values[:i]), sum(values[i:j]), sum(values[j:k]), sum(values[k:])]
        best = min(best, max(sums) - min(sums))
    return best


class Solutions(unittest.TestCase):
    def require(self):
        self.assertIsNotNone(shelf, 'First solution has not been implemented')
        self.assertIsNotNone(pipe, 'Second solution has not been implemented')

    def test_article_samples(self):
        self.require()
        for a, d, expected in [([1, 2, 3], 1, 4), ([8, 1], 1, 1), ([4, 4, 4], 10, 6)]:
            self.assertEqual(shelf.count_arrangements(a, d), expected)
        for a, expected in [([4, 5, 1, 2, 8], 5), ([1, 1, 1, 1], 0), ([9, 1, 1, 1, 1], 8)]:
            self.assertEqual(pipe.min_range(a), expected)

    def test_shelf_against_identity_permutations(self):
        self.require()
        count = 0
        for n in range(2, 6):
            for values in itertools.product(range(1, 4), repeat=n):
                for d in (1, 2, 3):
                    self.assertEqual(shelf.count_arrangements(values, d), brute_shelf(values, d), (values, d))
                    count += 1
        rng = random.Random(906)
        for _ in range(80):
            a = [rng.randint(1, 15) for _ in range(rng.randint(2, 8))]
            d = rng.randint(1, 12)
            self.assertEqual(shelf.count_arrangements(a, d), brute_shelf(a, d), (a, d))
            count += 1
        print(f'Shelf oracle comparisons: {count}')

    def test_pipe_against_all_three_cuts(self):
        self.require()
        count = 0
        for n in range(4, 9):
            for values in itertools.product((1, 2, 7), repeat=n):
                self.assertEqual(pipe.min_range(values), brute_pipe(values), values)
                count += 1
        rng = random.Random(907)
        for _ in range(500):
            a = [rng.randint(1, 10**9) for _ in range(rng.randint(4, 20))]
            self.assertEqual(pipe.min_range(a), brute_pipe(a), a)
            count += 1
        print(f'Pipe oracle comparisons: {count}')

    def test_acm_and_limits(self):
        self.require()
        for folder in ('01-层板限差', '02-管材四切'):
            for case in json.loads((SESSION / folder / 'cases.json').read_text()):
                run = subprocess.run([sys.executable, str(SESSION / folder / 'solution.py')], input=case['stdin'], text=True, capture_output=True, timeout=3)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stdout.split(), case['expected'].split(), case['name'])
        from math import factorial
        self.assertEqual(shelf.count_arrangements([10**6] * 200000, 1), factorial(200000) % 998244353)
        self.assertEqual(pipe.min_range([10**9] * 100000), 0)
        self.assertEqual(pipe.min_range([1, 1, 1, 10**9]), 999999999)


if __name__ == '__main__':
    unittest.main(verbosity=2)
