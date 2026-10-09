---
layout: default
title: "Reducer：列表为什么会重复"
description: "对比覆盖字段与追加字段的更新规则"
eyebrow: "LangGraph 实验课 / 02"
---

# Reducer：列表为什么会重复

节点明明只生成一条新记录，历史里却出现重复内容，问题常出在合并规则。只看最终列表，很难分清是节点多跑了，还是旧数据被追加了两次。

## 只看这个机制

**Reducer 决定如何把旧值和本次更新合并。** 普通字段按更新覆盖；`Annotated[list[str], operator.add]` 把两个列表相加。每个字段独立选择规则。

因此 latest 表示当前值，history 表示累积记录，两者即使来自同一个节点也有不同含义。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_02.py`。导入、状态、节点和连线都在这个文件里。

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    latest: str
    history: Annotated[list[str], operator.add]

def first(state: State) -> dict:
    return {"latest": "A", "history": ["A"]}

def second(state: State) -> dict:
    return {"latest": "B", "history": ["B"]}

builder = StateGraph(State)
builder.add_node("first", first)
builder.add_node("second", second)
builder.add_edge(START, "first")
builder.add_edge("first", "second")
builder.add_edge("second", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"latest": "", "history": []})
    print("latest:", result["latest"])
    print("history:", result["history"])
    assert result["latest"] == "B"
    assert result["history"] == ["A", "B"]
```

运行：

```bash
python lesson_02.py
```

## 读懂结果

```text
latest: B
history: ['A', 'B']
```

first 写 A，second 写 B。latest 最终只剩 B，history 保留 A、B。second 返回的是新增的 `["B"]`，没有再次携带旧历史。

### 代码抓住三处

1. `latest: str` 没有 reducer，后来的更新替换旧值。
2. `history: Annotated[..., operator.add]` 将旧列表与本次返回值拼接。
3. `second` 只返回新增记录，框架负责把它合并进历史。

## 动手改一处

把 second 返回的 history 改为 `state["history"] + ["B"]`，结果会变成 `["A", "A", "B"]`。再改为 `[]`，历史会保留 A，而不是清空。同步修改原断言。

## 最容易踩的坑

返回完整 State 并非一律语法非法，但追加字段会把已有值再合并一次。需要替换或重置时，要选符合业务语义的更新方式。

## 记住这一点

**追加字段返回增量；不要把全量历史伪装成新增记录。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [消息 ID：追加一条还是修订一条](../03-message-ids/index.html)
