---
layout: default
title: "[codex] 异步并行、汇合屏障与 Send"
description: "从固定分支走到动态任务分发并验证汇总结果"
eyebrow: "LangGraph / 11"
---

# [codex] 异步并行、汇合屏障与 Send

同时查两个接口很容易写成并行，但如果汇总节点只拿到一半结果，或者两个分支都覆盖同一字段，最终报告就不可信。并行图要同时设计启动方式、结果合并方式和等待条件。

## 三个问题分开看

| 问题 | 对应机制 | 实验 |
|---|---|---|
| 固定的两个任务怎样一起启动 | 从同一节点向两边连线 | 10、15 |
| 两个任务怎样写回结果 | 独立字段或 reducer | 10、15 |
| 输入有多少项才知道任务数量 | `Send` 动态生成任务 | 16 |

同一超步多个节点写同一普通字段，会出现并发更新冲突，不能依赖“最后完成的覆盖之前的”。实验 10 的两个分支都写 values，所以使用追加 reducer；实验 15 分别写 words、chars，不需要给这两个字段加追加规则。

## 异步用于等待，屏障用于汇总

实验 10 的核心是这组连线；完整文件见下方练习索引：

```python
builder.add_edge(START, "left")
builder.add_edge(START, "right")
builder.add_edge(["left", "right"], "collect")
```

列表形式的起点明确要求两个分支都完成。即便以后某条支路增加节点，也应重新检查屏障等待的是不是各支路真正的终点。

节点使用 `async def` 等待 I/O 时，用 `await graph.ainvoke(...)` 或 `async for ... in graph.astream(...)` 驱动。实验通过两次独立执行分别展示这两个入口，不是在同一次执行上读取两份结果。CPU 密集计算不会仅因为加上 async 就变快。

## 动态任务：注册一个节点，执行多份任务

假设输入是 `[2, 3, 4]`，需要分别平方再求和。预先注册三个不同节点会把图结构和数据长度绑死。实验 16 只注册一次 square，每个 Send 携带一份 WorkerState：

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

结果为平方和 29；输入为空时结果为 0。父图的 State 包含 numbers、squares、total，而 worker 只收到自己的 number。不要在 worker 中假定所有父状态字段都存在。

这个例子的每个动态任务都只有一个 square 步骤，其结果合并后进入 collect。若将 worker 改成不同长度的复杂流程，要重新设计完成条件，不能照搬单步示例就认定所有嵌套任务都会按预期汇合。

## 空任务与顺序

空列表必须有明确路径；这里直接去 collect，且初始输入显式包含 `squares=[]`。若图带检查点并复用同一 thread，追加空列表不会清除旧 squares，需要重新设计每轮结果的存储或重置方式。

结果列表不应充当完成时序证据。需要按输入顺序展示时，在每个结果中附带索引，再在汇总节点排序；需要限流时，还要设置与下游容量匹配的并发策略。Send 描述任务分发，不自动代表跨机器的任务队列。

## 动手验证

依次运行 10、15、16。把实验 10 的 right 改成返回 10，total 应为 15；实验 15 输入改为 `hello world`，应得到两个词、11 个字符；实验 16 改成 `[1, 2, 3, 4]`，平方和应为 30。保留一次空列表验证，避免只测正常路径。

## 配套练习

运行命令均以 `examples/langgraph-mini-lab` 为当前目录；可点击文件查看完整源码。

| 实验 | 可运行文件 | 观察重点 |
|---|---|---|
| 10 | [异步并行与等待汇总](../../examples/langgraph-mini-lab/03_nodes/10_parallel_async.py) | async/await、ainvoke/astream、共享字段 reducer、列表形式汇合边 |
| 15 | [四节点菱形汇总](../../examples/langgraph-mini-lab/04_nodes/15_diamond.py) | 先准备数据再并行；并行写不同字段不需要追加 reducer |
| 16 | [Send 动态分发](../../examples/langgraph-mini-lab/04_nodes/16_send_map_reduce.py) | 节点定义数固定，Send 任务数动态；worker 接收自己的小状态 |

## 小结

- 并发写同一字段先定义合并语义，写不同字段先明确所有权。
- 固定分支使用明确的汇合屏障，互斥分支不能套用它。
- 动态分发要处理零任务、结果顺序和跨轮状态累积。

机制参考：[Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)、[Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [[codex] 工具闭环与模型上下文](../12-codex-tool-loop/index.html)
