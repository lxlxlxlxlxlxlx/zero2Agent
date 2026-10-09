---
layout: default
title: "条件边：让状态决定下一步"
description: "分离状态更新与条件路由职责"
eyebrow: "LangGraph 实验课 / 04"
---

# 条件边：让状态决定下一步

同一份申请，分数达标就通过，否则拒绝。把判断散落在多个节点里，容易出现两边都执行或都不执行；路由规则应能单独读懂。

## 只看这个机制

**节点写结果，路由函数选标签，path_map 把标签映射到节点。** check 只计算 passed；route 返回 yes 或 no；图再选择 allow 或 reject。路由函数不算注册的业务节点。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_04.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    score: int
    passed: bool
    result: str

def check(state: State) -> dict:
    return {"passed": state["score"] >= 60}

def route(state: State) -> str:
    return "yes" if state["passed"] else "no"

def allow(state: State) -> dict:
    return {"result": "通过"}

def reject(state: State) -> dict:
    return {"result": "不通过"}

builder = StateGraph(State)
builder.add_node("check", check)
builder.add_node("allow", allow)
builder.add_node("reject", reject)
builder.add_edge(START, "check")
builder.add_conditional_edges("check", route, {"yes": "allow", "no": "reject"})
builder.add_edge("allow", END)
builder.add_edge("reject", END)
graph = builder.compile()

if __name__ == "__main__":
    for score, expected in [(75, "通过"), (40, "不通过")]:
        result = graph.invoke({"score": score})
        print(f"{score}: {result['result']}")
        assert result["result"] == expected
```

运行：

```bash
python lesson_04.py
```

## 读懂结果

```text
75: 通过
40: 不通过
```

75 走 allow，40 走 reject。一次输入只经过一个结果节点，不需要等另一条互斥分支也完成。

### 代码抓住三处

1. `check` 先提交 passed 字段，路由读取的是更新后的状态。
2. `route` 返回标签，映射表决定标签对应哪个实际节点。
3. 两个分支分别连接 END，表示任意一条路径完成即可结束。

## 动手改一处

将通过阈值改为 80，75 和 40 都应返回“不通过”。修改对应的 expected 后再次运行。

## 最容易踩的坑

标签与映射必须一致。不要在 route 里原地改 State；数据修改应通过节点返回值提交。互斥分支也不能接到一个等待两边都完成的列表屏障。

## 记住这一点

**状态告诉路由发生了什么，路由只回答接下来去哪。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [循环：把停止条件写进图](../05-bounded-loops/index.html)
