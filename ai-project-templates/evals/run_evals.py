"""Run a dataset through a target function and grade it.

Usage: python run_evals.py --target rag_app.answer:answer --dataset datasets/rag_qa.jsonl
"""
import argparse
import importlib
import json
import time
from pathlib import Path

from dotenv import load_dotenv

from graders.code_graders import contains_all
from graders.llm_judge import judge

GRADERS = {"contains_all": contains_all, "llm_judge": judge}


def load_target(spec: str):
    module, func = spec.split(":")
    return getattr(importlib.import_module(module), func)


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True)
    p.add_argument("--dataset", required=True)
    args = p.parse_args()

    target = load_target(args.target)
    cases = [json.loads(l) for l in Path(args.dataset).read_text().splitlines() if l.strip()]
    results = []
    for case in cases:
        output = target(case["input"])
        grades = {name: g(output, case) for name, g in GRADERS.items()}
        results.append({"id": case["id"], "output": output, "grades": grades})
        status = "PASS" if all(ok for ok, _ in grades.values()) else "FAIL"
        print(f"{status}  {case['id']}")

    passed = sum(all(ok for ok, _ in r["grades"].values()) for r in results)
    print(f"\n{passed}/{len(results)} passed")
    out = Path("reports") / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
