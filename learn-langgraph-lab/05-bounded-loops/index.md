---
layout: default
title: "循环：把停止条件写进图"
description: "用回边与次数保护控制重复执行"
eyebrow: "LangGraph 实验课 / 05"
---

# 循环：把停止条件写进图

一次生成不够好，可以再做一轮；但“再试一次”如果没有退出条件，就会变成无限执行。先用确定性的字符串例子看清循环怎样停止。

## 只看这个机制

**回边允许节点重复执行，条件边决定继续还是退出。** write 每次追加一个“好”，check 检查长度，满足条件后直接进入 END。

状态里的 attempts 是业务次数；recursion_limit 限制的是图超步，一个业务循环可能经过多个超步。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_05.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    attempts: int
    passed: bool

def write(state: State) -> dict:
    return {"text": state["text"] + "好", "attempts": state["attempts"] + 1}

def check(state: State) -> dict:
    return {"passed": len(state["text"]) >= 2}

def route(state: State) -> str:
    return END if state["passed"] else "write"

builder = StateGraph(State)
builder.add_node("write", write)
builder.add_node("check", check)
builder.add_edge(START, "write")
builder.add_edge("write", "check")
builder.add_conditional_edges("check", route, ["write", END])
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"text": "", "attempts": 0}, {"recursion_limit": 20})
    print(f"{result['text']}，尝试 {result['attempts']} 次")
    assert result["attempts"] == 2 and result["passed"]
```

运行：

```bash
python lesson_05.py
```

## 读懂结果

```text
好好，尝试 2 次
```

write 执行两次，text 变成“好好”，随后退出。框架没有替业务判断文章质量，达标条件完全由 check 给出。

### 代码抓住三处

1. `write → check` 是一轮业务尝试，attempts 每轮只增加一次。
2. 不满足条件时回到 write；满足时进入 END，不再回到循环。
3. `recursion_limit` 是运行保护参数，不是 State 字段，也不是业务尝试数。

## 动手改一处

把长度阈值从 2 改成 3，预期 attempts 为 3。再把条件改成永远不成立，观察超步上限抛出的异常，不能把这种结束当成业务成功。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

真实生成还要设置业务尝试、耗时或费用上限。这里的长度条件保证正常输入终止，recursion_limit 只提供失控兜底，不能等价为工具调用预算。

## 记住这一点

**先定义成功、失败和预算耗尽三种出口，再添加回边。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [状态流：看更新还是看完整快照](../06-state-streaming/index.html)
