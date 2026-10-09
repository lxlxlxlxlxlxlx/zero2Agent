---
layout: default
title: "Command：更新状态并选择后继"
description: "在一个返回值里表达更新与跳转"
eyebrow: "LangGraph 实验课 / 10"
---

# Command：更新状态并选择后继

紧急任务既要记录走了哪条路线，又要立即进入快速通道。分两处写这两个决定，容易让状态与真实路径不一致。

## 只看这个机制

**Command(update=..., goto=...) 同时表达数据更新与后继节点。** 返回类型里的 Literal 列出允许的目标，便于读代码和展示图结构。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_10.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

class State(TypedDict):
    urgent: bool
    route: str
    text: str

def choose(state: State) -> Command[Literal["fast", "normal"]]:
    target = "fast" if state["urgent"] else "normal"
    return Command(update={"route": target}, goto=target)

def fast(state: State) -> dict:
    return {"text": "加急处理"}

def normal(state: State) -> dict:
    return {"text": "普通处理"}

builder = StateGraph(State)
builder.add_node("choose", choose)
builder.add_node("fast", fast)
builder.add_node("normal", normal)
builder.add_edge(START, "choose")
builder.add_edge("fast", END)
builder.add_edge("normal", END)
graph = builder.compile()

if __name__ == "__main__":
    urgent = graph.invoke({"urgent": True})
    normal_result = graph.invoke({"urgent": False})
    print(f"{urgent['route']}: {urgent['text']}")
    print(f"{normal_result['route']}: {normal_result['text']}")
    assert urgent["text"] == "加急处理"
    assert normal_result["text"] == "普通处理"
```

运行：

```bash
python lesson_10.py
```

## 读懂结果

```text
fast: 加急处理
normal: 普通处理
```

urgent=True 进入 fast，False 进入 normal。输出中的路线字段与所执行分支一致；格式化输出在图外完成，不为打印结果增加节点。

### 代码抓住三处

1. choose 在同一个 Command 中写 route 并选择 goto。
2. fast 与 normal 都是正常业务节点，它们只返回各自的处理结果。
3. choose 不再配置静态出边，避免一次决定又触发另一个固定目标。

## 动手改一处

把首次调用的 urgent 改为 False，应得到 `normal: 普通处理`。在分支内临时打印节点名，确认每次只执行一边。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

goto 不会撤销静态边。给 choose 再加固定出边可能触发额外路径；如果只想二选一，就保留一种出边决策方式。

## 记住这一点

**一个业务决定同时改变数据和路线时，让它们一起返回。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [工具闭环：请求、执行、结果回填](../11-tool-loop/index.html)
