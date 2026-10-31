"""Execute every backtracking/DP reference as a standalone ACM program."""

import ast
import json
from pathlib import Path
import subprocess
import sys

from verify_dp import assert_output


ROOT = Path(__file__).resolve().parents[1]


def main():
    questions = json.loads((ROOT / "data/dp.json").read_text())
    references = json.loads((ROOT / "data/references-dp.json").read_text())
    assert [r["id"] for r in references] == [q["id"] for q in questions]
    count = 0
    for question, reference in zip(questions, references):
        label = question["id"]
        assert reference["author"] == "灵茶山艾府", label
        assert reference["sourceUrl"].startswith(question["url"] + "solution"), label
        assert reference["sourceTitle"] and reference["variant"] and reference["note"], label
        assert reference["verifiedAt"] == "2026-09-15", label
        tree = ast.parse(reference["code"])
        imports = [ast.unparse(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        assert imports == [item["code"] for item in reference["imports"]], label
        assert all(item["purpose"] for item in reference["imports"]), label
        assert "NotImplementedError" not in reference["code"], label
        for case in question["cases"]:
            result = subprocess.run(
                [sys.executable, "-I", "-c", reference["code"]],
                input=case["stdin"], text=True, capture_output=True, timeout=10,
            )
            assert result.returncode == 0, f"{label}: {result.stderr}"
            assert_output(result.stdout, case["expected"], question["judge"], f"{label} / {case['name']}")
            count += 1
    print(f"Verified {len(references)} standalone references, {count} fixture cases, and complete import metadata.")


if __name__ == "__main__":
    main()
