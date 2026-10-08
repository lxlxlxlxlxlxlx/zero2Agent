"""逐个独立运行主练习，比对标准输出，并执行练习内部的 assert。"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", action="store_true", help="同时验证第 20 课跨进程恢复")
    parser.add_argument("--verbose", action="store_true", help="显示每个例子的标准输出")
    args = parser.parse_args()
    missing = [name for name in ("langgraph", "langchain_core", "pydantic") if not available(name)]
    if missing:
        print("未运行测试，缺少依赖:", ", ".join(missing))
        print("请先运行: python -m pip install -r requirements.txt")
        return 2
    if args.sqlite and not available("langgraph.checkpoint.sqlite"):
        print("未运行测试，请先运行: python -m pip install -r requirements-sqlite.txt")
        return 2
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    passed, failed, skipped = 0, 0, 0
    with tempfile.TemporaryDirectory(prefix="langgraph-mini-lab-") as data_dir:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                   PYTHONDONTWRITEBYTECODE="1", LANGSMITH_TRACING="false",
                   LANGCHAIN_TRACING_V2="false", LANGGRAPH_LAB_DATA_DIR=data_dir)
        env.pop("PYTHONOPTIMIZE", None)  # 保证子进程中的 assert 没有被禁用。
        for item in manifest:
            if item["dependency"] == "sqlite" and not args.sqlite:
                print("SKIP:", item["path"], "（使用 --sqlite 加测）")
                skipped += 1
                continue
            modes = [["start"], ["status"], ["resume"], ["status"]] if item["dependency"] == "sqlite" else [[]]
            output, problem = "", ""
            for mode in modes:
                try:
                    result = subprocess.run([sys.executable, str(ROOT / item["path"]), *mode],
                                            cwd=ROOT, env=env, capture_output=True,
                                            text=True, encoding="utf-8", timeout=30)
                except (subprocess.TimeoutExpired, OSError) as error:
                    problem = str(error)
                    break
                output += result.stdout
                if result.returncode:
                    problem = result.stderr or result.stdout or f"退出码 {result.returncode}"
                    break
            if not problem and output.strip() != item["expected"].strip():
                problem = f"输出与预期不一致。\n预期:\n{item['expected']}实际:\n{output}"
            if problem:
                failed += 1
                print("FAIL:", item["path"])
                print(problem)
            else:
                passed += 1
                print("PASS:", item["path"])
                if args.verbose:
                    print(output, end="")
    print(f"结果: {passed} 通过，{failed} 失败，{skipped} 跳过。")
    print("真实模型示例 22 不在自测范围内。")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
