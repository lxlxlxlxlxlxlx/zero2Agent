---
layout: default
title: "[codex] 异步并行、汇合屏障与 Send"
description: "从固定分支走到动态任务分发并验证汇总结果"
eyebrow: "LangGraph / 11"
---

# [codex] 异步并行、汇合屏障与 Send

同时查两个接口很容易写成并行，但如果汇总节点只拿到一半结果，或者两个分支都覆盖同一字段，最终报告就不可信。并行图要同时设计启动方式、结果合并方式和等待条件。

## 运行准备

在自己新建的练习目录中运行以下命令；本页所有实验代码都已完整展开，可以直接复制保存，不需要下载源码或依赖原始资料目录。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "langgraph==1.2.12" "langchain-core>=1.0,<2.0" "pydantic>=2.7.4,<3.0"
```

建议 Python 3.11 或以上；fish 用户用 `source .venv/bin/activate.fish` 激活。已在前一篇创建环境的读者可以继续使用同一环境。核心版本用于复现实验，其余依赖是范围约束；主练习不需要模型 API Key。

## 三个问题分开看

| 问题 | 对应机制 | 实验 |
|---|---|---|
| 固定的两个任务怎样一起启动 | 从同一节点向两边连线 | 10、15 |
| 两个任务怎样写回结果 | 独立字段或 reducer | 10、15 |
| 输入有多少项才知道任务数量 | `Send` 动态生成任务 | 16 |

同一超步多个节点写同一普通字段，会出现并发更新冲突，不能依赖“最后完成的覆盖之前的”。实验 10 的两个分支都写 values，所以使用追加 reducer；实验 15 分别写 words、chars，不需要给这两个字段加追加规则。

## 异步用于等待，屏障用于汇总

实验 10 同时启动两个异步节点，并等待它们都完成后汇总：

### 实验 10：异步并行与等待汇总 {#experiment-10}

将下面的完整代码保存为 `10_parallel_async.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
import asyncio
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    values: Annotated[list[int], operator.add]
    total: int

async def left(state: State) -> dict:
    await asyncio.sleep(0.02)
    return {"values": [5]}

async def right(state: State) -> dict:
    await asyncio.sleep(0.01)
    return {"values": [8]}

def collect(state: State) -> dict:
    return {"total": sum(state["values"])}

builder = StateGraph(State)
builder.add_node("left", left)
builder.add_node("right", right)
builder.add_node("collect", collect)
builder.add_edge(START, "left")
builder.add_edge(START, "right")
builder.add_edge(["left", "right"], "collect")
builder.add_edge("collect", END)
graph = builder.compile()

async def main() -> None:
    result = await graph.ainvoke({"values": []})
    print("ainvoke:", result["total"])
    snapshots = []
    async for snapshot in graph.astream({"values": []}, stream_mode="values"):
        snapshots.append(snapshot)
    print("astream:", snapshots[-1]["total"])
    assert sorted(result["values"]) == [5, 8]
    assert result["total"] == snapshots[-1]["total"] == 13

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python 10_parallel_async.py
```

预期输出：

```text
ainvoke: 13
astream: 13
```

列表形式的起点明确要求两个分支都完成。即便以后某条支路增加节点，也应重新检查屏障等待的是不是各支路真正的终点。

节点使用 `async def` 等待 I/O 时，用 `await graph.ainvoke(...)` 或 `async for ... in graph.astream(...)` 驱动。实验通过两次独立执行分别展示这两个入口，不是在同一次执行上读取两份结果。CPU 密集计算不会仅因为加上 async 就变快。

## 菱形图：并行写不同字段

实验 15 先清理文本，再分别统计单词数和字符数，最后生成报告。两个分支写不同字段，所以不需要追加 reducer；汇总仍显式等待两个分支。

### 实验 15：四节点菱形汇总 {#experiment-15}

将下面的完整代码保存为 `15_diamond.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    words: int
    chars: int
    report: str

def prepare(state: State) -> dict:
    return {"text": state["text"].strip()}

def count_words(state: State) -> dict:
    return {"words": len(state["text"].split())}

def count_chars(state: State) -> dict:
    return {"chars": len(state["text"])}

def make_report(state: State) -> dict:
    return {"report": f"单词 {state['words']}，字符 {state['chars']}"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("count_words", count_words)
builder.add_node("count_chars", count_chars)
builder.add_node("make_report", make_report)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "count_words")
builder.add_edge("prepare", "count_chars")
builder.add_edge(["count_words", "count_chars"], "make_report")
builder.add_edge("make_report", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"text": " hi hi "})
    print(result["report"])
    assert (result["words"], result["chars"]) == (2, 5)
```

运行：

```bash
python 15_diamond.py
```

预期输出：

```text
单词 2，字符 5
```

## 动态任务：注册一个节点，执行多份任务

假设输入是 `[2, 3, 4]`，需要分别平方再求和。预先注册三个不同节点会把图结构和数据长度绑死。实验 16 只注册一次 square，每个 Send 携带一份 WorkerState：

### 实验 16：Send 动态分发 {#experiment-16}

将下面的完整代码保存为 `16_send_map_reduce.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    numbers: list[int]
    tasks: list[int]
    squares: Annotated[list[int], operator.add]
    total: int
    report: str

class WorkerState(TypedDict):
    number: int

def prepare(state: State) -> dict:
    return {"tasks": state["numbers"]}

def dispatch(state: State):
    if not state["tasks"]:
        return "collect"
    return [Send("square", {"number": n}) for n in state["tasks"]]

def square(state: WorkerState) -> dict:
    return {"squares": [state["number"] ** 2]}

def collect(state: State) -> dict:
    return {"total": sum(state["squares"])}

def make_report(state: State) -> dict:
    return {"report": f"平方和: {state['total']}"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("square", square)
builder.add_node("collect", collect)
builder.add_node("make_report", make_report)
builder.add_edge(START, "prepare")
builder.add_conditional_edges("prepare", dispatch, ["square", "collect"])
builder.add_edge("square", "collect")
builder.add_edge("collect", "make_report")
builder.add_edge("make_report", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"numbers": [2, 3, 4], "squares": []})
    empty = graph.invoke({"numbers": [], "squares": []})
    print(result["report"])
    print("空任务:", empty["total"])
    assert sorted(result["squares"]) == [4, 9, 16]
    assert result["total"] == 29 and empty["total"] == 0
```

运行：

```bash
python 16_send_map_reduce.py
```

预期输出：

```text
平方和: 29
空任务: 0
```

结果为平方和 29；输入为空时结果为 0。父图的 State 包含 numbers、squares、total，而 worker 只收到自己的 number。不要在 worker 中假定所有父状态字段都存在。

这个例子的每个动态任务都只有一个 square 步骤，其结果合并后进入 collect。若将 worker 改成不同长度的复杂流程，要重新设计完成条件，不能照搬单步示例就认定所有嵌套任务都会按预期汇合。

## 空任务与顺序

空列表必须有明确路径；这里直接去 collect，且初始输入显式包含 `squares=[]`。若图带检查点并复用同一 thread，追加空列表不会清除旧 squares，需要重新设计每轮结果的存储或重置方式。

结果列表不应充当完成时序证据。需要按输入顺序展示时，在每个结果中附带索引，再在汇总节点排序；需要限流时，还要设置与下游容量匹配的并发策略。Send 描述任务分发，不自动代表跨机器的任务队列。

## 动手验证

依次运行 10、15、16。把实验 10 的 right 改成返回 10，total 应为 15；实验 15 输入改为 `hello world`，应得到两个词、11 个字符；实验 16 改成 `[1, 2, 3, 4]`，平方和应为 30。保留一次空列表验证，避免只测正常路径。

## 本页实验回顾

| 实验 | 已展开的内容 |
|---|---|
| 10 | 异步并行与等待汇总 |
| 15 | 四节点菱形汇总 |
| 16 | Send 动态分发 |

## 小结

- 并发写同一字段先定义合并语义，写不同字段先明确所有权。
- 固定分支使用明确的汇合屏障，互斥分支不能套用它。
- 动态分发要处理零任务、结果顺序和跨轮状态累积。

机制参考：[Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)、[Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [[codex] 工具闭环与模型上下文](../12-codex-tool-loop/index.html)
