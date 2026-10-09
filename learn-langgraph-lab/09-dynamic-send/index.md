---
layout: default
title: "Send：按输入数量分发任务"
description: "让一个 worker 节点接收多份独立输入"
eyebrow: "LangGraph 实验课 / 09"
---

# Send：按输入数量分发任务

输入有三个数字就平方三次，有一百个就平方一百次。如果为每项注册一个节点，图结构会跟着数据长度变化。

## 只看这个机制

**Send 把节点定义与任务数量分开。** 图只注册一次 square，路由函数为每个数字创建一份任务；worker 只接收自己的 number，结果通过 squares 的 reducer 汇总。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_09.py`。导入、状态、节点和连线都在这个文件里。

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    numbers: list[int]
    squares: Annotated[list[int], operator.add]
    total: int

class WorkerState(TypedDict):
    number: int

def dispatch(state: State):
    if not state["numbers"]:
        return "collect"
    return [Send("square", {"number": n}) for n in state["numbers"]]

def square(state: WorkerState) -> dict:
    return {"squares": [state["number"] ** 2]}

def collect(state: State) -> dict:
    return {"total": sum(state["squares"])}

builder = StateGraph(State)
builder.add_node("square", square)
builder.add_node("collect", collect)
builder.add_conditional_edges(START, dispatch, ["square", "collect"])
builder.add_edge("square", "collect")
builder.add_edge("collect", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"numbers": [2, 3, 4], "squares": []})
    empty = graph.invoke({"numbers": [], "squares": []})
    print(f"平方和: {result['total']}")
    print("空任务:", empty["total"])
    assert sorted(result["squares"]) == [4, 9, 16]
    assert result["total"] == 29 and empty["total"] == 0
```

运行：

```bash
python lesson_09.py
```

## 读懂结果

```text
平方和: 29
空任务: 0
```

三个任务得到 4、9、16，合计 29；空输入直接去 collect，结果为 0。每个 worker 都只有一个计算步骤；任务直接从 START 分发。

### 代码抓住三处

1. START 的条件路由直接遍历 numbers，空列表单独转入 collect。
2. 每个 `Send("square", {"number": n})` 提交一次独立的 worker 调用。
3. square 返回一项列表，reducer 收集多份结果，collect 最后统一求和。

## 动手改一处

输入改为 `[1, 2, 3, 4]`，square 会执行四次，平方和为 30。仍保留一次空列表调用，检查零任务出口。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

worker 收到的是 Send 中的小状态，不能假定拥有全部父图字段。需要展示输入顺序时携带索引并排序；Send 也不自动意味着跨机器任务队列。

## 记住这一点

**节点可以只有一份定义，任务可以有多份输入。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [Command：更新状态并选择后继](../10-command-routing/index.html)
