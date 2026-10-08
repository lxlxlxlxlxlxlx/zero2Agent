# [codex] LangGraph 最小实验

本目录包含 21 个主练习和 1 个真实模型选学例子。

完整运行说明、知识点映射、验证记录与教学文章链接见 [实验入口](index.md)。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-sqlite.txt
python check_syntax.py
python run_all.py --sqlite
```

fish 使用 `source .venv/bin/activate.fish`。所有命令在本目录运行。

核心基线为 LangGraph 1.2.12。主练习已在 Python 3.11.12 下全部通过；真实模型例子未运行，不计入自测结果。
