---
layout: default
title: "Checkpointer：同一会话延续，不同会话隔离"
description: "用 thread_id 找回已有图状态"
eyebrow: "LangGraph 实验课 / 14"
---

# Checkpointer：同一会话延续，不同会话隔离

用户再次发起请求，希望沿用上一次的任务状态；另一个用户却应从零开始。仅复用同一个 graph 对象，不能替代会话标识。

## 只看这个机制

**Checkpointer 保存图状态，thread_id 用于关联同一会话。** 本例只累加 count，分别调用 A、A、B，直接观察状态复用和隔离。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_14.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    label: str
    count: int

def increment(state: State) -> dict:
    return {"count": state.get("count", 0) + 1}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_edge(START, "increment")
builder.add_edge("increment", END)
graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    config_a = {"configurable": {"thread_id": "A"}}
    config_b = {"configurable": {"thread_id": "B"}}
    a1 = graph.invoke({"label": "A"}, config_a)
    a2 = graph.invoke({"label": "A"}, config_a)
    b1 = graph.invoke({"label": "B"}, config_b)
    for result in (a1, a2, b1):
        print(f"{result['label']}: {result['count']}")
    snapshot = graph.get_state(config_a)
    assert (a1["count"], a2["count"], b1["count"]) == (1, 2, 1)
    assert snapshot.values["count"] == 2 and snapshot.next == ()
```

运行：

```bash
python lesson_14.py
```

## 读懂结果

```text
A: 1
A: 2
B: 1
```

A 的两次调用得到 1、2，B 首次得到 1。第二次 A 只传 label，没有覆盖旧 count；get_state 查看已保存值，不推进图。

### 代码抓住三处

1. compile 时传入同一个保存器，才能让后续调用找回检查点。
2. config 中的 thread_id 定位会话；第二次调用不传 count，旧值才得以延续。
3. `get_state(config_a)` 读取已保存快照，next 为空说明当前没有待执行步骤。

## 动手改一处

把第二次调用改为 `graph.invoke({"label": "B"}, config_b)`，打印应变为 A: 1、B: 1、B: 2。计数断言改为 `(1, 1, 2)`，A 的快照计数改为 1。

## 最容易踩的坑

同一 thread 输入新字典是新一轮执行，不能与中断恢复混为一谈。InMemorySaver 随进程结束丢失；thread_id 也不是访问权限校验。

## 记住这一点

**会话标识找到旧状态，是否落盘还要看具体保存器。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/persistence)。

下一篇建议继续看：

- [Store：跨会话读取同一份用户资料](../15-store-memory/index.html)
