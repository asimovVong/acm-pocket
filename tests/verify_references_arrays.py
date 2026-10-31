"""Execute array references against page fixtures and independent small-case oracles."""
import contextlib
import io
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / 'data/arrays.json').read_text())
REFERENCES = {row['id']: row for row in json.loads((ROOT / 'data/references-arrays.json').read_text())}


def check_output(question, output, expected, stdin):
    rule = question['judge']
    if rule == 'peak':
        tokens = output.split()
        assert len(tokens) == 1
        index = int(tokens[0])
        values = list(map(int, stdin.split()))[1:]
        assert 0 <= index < len(values)
        assert index == 0 or values[index] > values[index - 1]
        assert index == len(values) - 1 or values[index] > values[index + 1]
    elif rule == 'tokens':
        assert output.split() == str(expected).split(), (output, expected)
    else:
        actual = json.loads(output)
        if isinstance(expected, str):
            expected = json.loads(expected)
        if rule == 'unordered-nested':
            actual = sorted(tuple(sorted(row)) for row in actual)
            expected = sorted(tuple(sorted(row)) for row in expected)
        assert actual == expected, (actual, expected)


def make_input(values, extra=None):
    first = str(len(values)) + ('' if extra is None else ' ' + str(extra))
    return first + '\n' + ' '.join(map(str, values)) + '\n'


def random_case(problem_id, rng):
    if problem_id == '3':
        text = ''.join(rng.choice('abA12 !') for _ in range(rng.randrange(12)))
        expected = max((j - i for i in range(len(text) + 1) for j in range(i, len(text) + 1) if len(set(text[i:j])) == j - i), default=0)
        return text + '\n', expected
    n = rng.randrange(1, 10)
    values = [rng.randrange(-8, 9) for _ in range(n)]
    if problem_id == '167':
        values = sorted(rng.sample(range(-20, 21), rng.randrange(2, 10)))
        by_sum = {}
        for i, j in itertools.combinations(range(len(values)), 2):
            by_sum.setdefault(values[i] + values[j], []).append([i + 1, j + 1])
        target = rng.choice([total for total, pairs in by_sum.items() if len(pairs) == 1])
        return make_input(values, target), by_sum[target][0]
    if problem_id == '15':
        values += [0] * max(0, 3 - len(values))
        triples = sorted({tuple(sorted(group)) for group in itertools.combinations(values, 3) if sum(group) == 0})
        return make_input(values), [list(group) for group in triples]
    if problem_id in {'11', '42'}:
        values = [rng.randrange(10) for _ in range(max(n, 2 if problem_id == '11' else 1))]
        if problem_id == '11':
            expected = max((j - i) * min(values[i], values[j]) for i, j in itertools.combinations(range(len(values)), 2))
        else:
            expected = sum(min(max(values[:i + 1]), max(values[i:])) - value for i, value in enumerate(values))
        return make_input(values), expected
    if problem_id in {'209', '713'}:
        values = [rng.randrange(1, 8) for _ in range(n)]
        target = rng.randrange(1 if problem_id == '209' else 0, 35)
        matches = []
        for i in range(n):
            total, product = 0, 1
            for j in range(i, n):
                total += values[j]
                product *= values[j]
                if (total >= target if problem_id == '209' else product < target):
                    matches.append(j - i + 1)
        expected = min(matches, default=0) if problem_id == '209' else len(matches)
        return make_input(values, target), expected
    if problem_id == '34':
        if rng.randrange(5) == 0:
            values = []
        values.sort()
        target = rng.randrange(-10, 11)
        matches = [i for i, value in enumerate(values) if value == target]
        return make_input(values, target), [matches[0], matches[-1]] if matches else [-1, -1]
    if problem_id == '162':
        for i in range(1, n):
            if values[i] == values[i - 1]:
                values[i] += 1
        return make_input(values), None
    if problem_id in {'153', '33'}:
        values = sorted(rng.sample(range(-20, 21), n))
        rotate = rng.randrange(n)
        values = values[rotate:] + values[:rotate]
        if problem_id == '153':
            return make_input(values), min(values)
        target = rng.choice(values) if rng.randrange(2) else rng.randrange(-25, 26)
        return make_input(values, target), values.index(target) if target in values else -1
    if problem_id == '739':
        values = [rng.randrange(30, 101) for _ in range(n)]
        expected = [next((j - i for j in range(i + 1, n) if values[j] > value), 0) for i, value in enumerate(values)]
        return make_input(values), expected
    if problem_id == '239':
        k = rng.randrange(1, n + 1)
        return make_input(values, k), [max(values[i:i + k]) for i in range(n - k + 1)]
    raise AssertionError(problem_id)


def main():
    assert set(REFERENCES) == {row['id'] for row in QUESTIONS}
    fixture_count = 0
    random_count = 0
    rng = random.Random(20260915)
    for question in QUESTIONS:
        reference = REFERENCES[question['id']]
        code = reference['code']
        assert reference['author'] == '灵茶山艾府'
        assert '/solutions/' in reference['sourceUrl']
        for case in question['cases']:
            run = subprocess.run([sys.executable, '-c', code], input=case['stdin'], capture_output=True, text=True, timeout=3, check=True)
            assert not run.stderr, run.stderr
            check_output(question, run.stdout, case['expected'], case['stdin'])
            fixture_count += 1

        namespace = {'__name__': '__reference_test__'}
        exec(compile(code, '<reference ' + question['id'] + '>', 'exec'), namespace)
        for _ in range(100):
            stdin, expected = random_case(question['id'], rng)
            stream = io.TextIOWrapper(io.BytesIO(stdin.encode()), encoding='utf-8')
            output = io.StringIO()
            saved_stdin = sys.stdin
            try:
                sys.stdin = stream
                with contextlib.redirect_stdout(output):
                    namespace['solve']()
            finally:
                sys.stdin = saved_stdin
                stream.close()
            check_output(question, output.getvalue(), expected, stdin)
            random_count += 1
        print(f"{question['id']}: {len(question['cases'])} fixtures and 100 random cases passed")
    print(f'{len(QUESTIONS)} array references: {fixture_count} fixtures + {random_count} random oracle cases passed')


if __name__ == '__main__':
    main()
