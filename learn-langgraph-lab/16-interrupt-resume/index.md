---
layout: default
title: "Interrupt：等待审批，再继续执行"
description: "观察暂停点与恢复时的节点重入"
eyebrow: "LangGraph 实验课 / 16"
---

# Interrupt：等待审批，再继续执行

发布操作要等人工确认，审批者可能过一会儿才回来。把 Python 函数一直阻塞在输入上，无法让任务被可靠地找回和继续。

## 只看这个机制

**interrupt 提交待确认内容，Command(resume=...) 提供审批结果。** 图必须配置 checkpointer，并使用相同 thread_id 恢复。

恢复会重入中断所在节点，resume 值会成为 interrupt 的返回值。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_16.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

class State(TypedDict):
    request: str
    approved: bool
    result: str

def prepare(state: State) -> dict:
    return {"request": state["request"].strip()}

def approve(state: State) -> dict:
    print("进入审批")
    approved = interrupt({"request": state["request"]})
    if not isinstance(approved, bool):
        raise ValueError("审批结果必须是 True 或 False")
    return {"approved": approved}

def finish(state: State) -> dict:
    return {"result": "已批准" if state["approved"] else "已拒绝"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("approve", approve)
builder.add_node("finish", finish)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "approve")
builder.add_edge("approve", "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "approval-1"}}
    paused = graph.invoke({"request": " 发布草稿 "}, config)
    print("暂停:", paused["__interrupt__"][0].value)
    assert graph.get_state(config).next == ("approve",)
    result = graph.invoke(Command(resume=True), config)
    print(result["result"])
    assert result["approved"] is True
    assert graph.get_state(config).next == ()
```

运行：

```bash
python lesson_16.py
```

## 读懂结果

```text
进入审批
暂停: {'request': '发布草稿'}
进入审批
已批准
```

“进入审批”打印两次：第一次运行到中断，第二次从 approve 开头重跑。next 在暂停时指向 approve，完成后为空。

### 代码抓住三处

1. 第一次 invoke 返回中断信息，同时将暂停位置写入检查点。
2. 第二次 invoke 传 `Command(resume=True)`，沿同一 thread 恢复。
3. approve 从头重入，interrupt 返回恢复值；finish 再根据布尔结果决定文案。

## 动手改一处

把 resume 改为 False，结果应为“已拒绝”，同时把 approved 的断言改为 False。不要用字符串 `"False"` 代替布尔值。

## 最容易踩的坑

不要在 interrupt 前无保护地扣款或发消息，重入可能重复副作用；也不要用宽泛异常捕获吞掉中断控制信号。没有待执行节点不等于审批通过。

## 记住这一点

**中断保存的是可继续的任务，恢复会重新进入节点。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/interrupts)。

下一篇建议继续看：

- [SQLite：退出程序后恢复暂停任务](../17-sqlite-resume/index.html)
