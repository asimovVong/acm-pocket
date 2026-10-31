"""Exercise shipped reference programs through the same adapter as the browser."""
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runner import execute_code

results = []
for group in ['arrays', 'structures', 'dp']:
    questions = json.loads((ROOT / f'data/{group}.json').read_text())
    references = {r['id']: r for r in json.loads((ROOT / f'data/references-{group}.json').read_text())}
    for question in questions:
        reference = references[question['id']]
        tree = ast.parse(reference['code'])
        code_imports = {ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))}
        listed_imports = {item['code'] for item in reference['imports']}
        assert code_imports == listed_imports, (question['id'], code_imports, listed_imports)
        for index, fixture in enumerate(question['cases']):
            result = execute_code(reference['code'], fixture['stdin'], 8 * 1024 * 1024)
            results.append({'id': question['id'], 'index': index, **result})
print(json.dumps(results, ensure_ascii=False))
