---
layout: default
title: "状态流：看更新还是看完整快照"
description: "区分 updates 与 values 的观察视角"
eyebrow: "LangGraph 实验课 / 06"
---

# 状态流：看更新还是看完整快照

只拿最终结果 4，你看不出中间有没有先得到 2。排查多步流程时，通常需要知道哪个节点改了什么，以及合并后的状态是什么。

## 只看这个机制

**updates 看节点提交的变化，values 看状态快照。** 例子让 n 先加一再乘二，用同一张图分别演示两种观察方式。

下面两次 stream 调用是两轮执行；为了保持读取简单，使用默认 v1 返回格式。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_06.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    n: int

def increment(state: State) -> dict:
    return {"n": state["n"] + 1}

def double(state: State) -> dict:
    return {"n": state["n"] * 2}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_node("double", double)
builder.add_edge(START, "increment")
builder.add_edge("increment", "double")
builder.add_edge("double", END)
graph = builder.compile()

if __name__ == "__main__":
    updates = list(graph.stream({"n": 1}, stream_mode="updates"))
    values = list(graph.stream({"n": 1}, stream_mode="values"))
    print("updates:", updates)
    print("values:", values)
    assert updates == [{"increment": {"n": 2}}, {"double": {"n": 4}}]
    assert values == [{"n": 1}, {"n": 2}, {"n": 4}]
```

运行：

```bash
python lesson_06.py
```

## 读懂结果

```text
updates: [{'increment': {'n': 2}}, {'double': {'n': 4}}]
values: [{'n': 1}, {'n': 2}, {'n': 4}]
```

updates 有两项，对应 increment 和 double 的更新；values 有三项，包括初始 n=1，以及随后得到的 2、4。这是状态流，不是模型 Token 流。

### 代码抓住三处

1. 两次 `stream` 的输入相同，因此两轮执行过程可以直接对照。
2. `updates` 的键指出节点，值是该节点提交的局部更新。
3. `values` 展示合并后的状态；示例先转为列表便于观察，实时处理时可逐项遍历。

## 动手改一处

把两个调用的初始 n 都改成 3，updates 中的值应为 4、8，values 应为 3、4、8；同步修改断言。

## 最容易踩的坑

对有副作用的图，第二次 stream 会再次执行业务。显式切到 `version="v2"` 后，要按 `type/ns/data` 读取返回内容；不要只改参数却保留旧解析。

## 记住这一点

**观察视角和执行次数必须分开确认。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/streaming)。

下一篇建议继续看：

- [汇合屏障：等两个分支都完成](../07-fan-in/index.html)
