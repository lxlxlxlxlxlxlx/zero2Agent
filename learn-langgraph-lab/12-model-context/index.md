---
layout: default
title: "模型上下文：历史保存多少，本轮发送多少"
description: "把保留的消息与本轮输入分开管理"
eyebrow: "LangGraph 实验课 / 12"
---

# 模型上下文：历史保存多少，本轮发送多少

历史越长，全部发送给模型的成本越高；但为了缩短输入而删掉历史，又会丢失审计依据。保存和发送需要两套明确的规则。

## 只看这个机制

**messages 保留历史，model_input 表达本轮选择。** 例子只取系统消息和最新问题，模拟生成后再审计两者数量，避免把上下文裁剪等同于历史删除。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_12.py`。导入、状态、节点和连线都在这个文件里。

```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage
from langgraph.graph import MessagesState, StateGraph, START, END

class State(MessagesState):
    model_input: list[AnyMessage]
    history_count: int
    context_count: int

def select_context(state: State) -> dict:
    # 本例输入保证第一条是系统消息，最后一条是用户消息。
    return {"model_input": [state["messages"][0], state["messages"][-1]]}

def mock_model(state: State) -> dict:
    question = state["model_input"][-1].content
    return {"messages": [AIMessage(content=f"收到: {question}")]}

def audit(state: State) -> dict:
    return {"history_count": len(state["messages"]),
            "context_count": len(state["model_input"])}

builder = StateGraph(State)
builder.add_node("select_context", select_context)
builder.add_node("mock_model", mock_model)
builder.add_node("audit", audit)
builder.add_edge(START, "select_context")
builder.add_edge("select_context", "mock_model")
builder.add_edge("mock_model", "audit")
builder.add_edge("audit", END)
graph = builder.compile()

if __name__ == "__main__":
    history = [SystemMessage(content="请简短回答"),
               HumanMessage(content="第一问"), AIMessage(content="第一答"),
               HumanMessage(content="第二问"), AIMessage(content="第二答"),
               HumanMessage(content="第三问")]
    result = graph.invoke({"messages": history})
    print("history_count:", result["history_count"])
    print("context_count:", result["context_count"])
    assert result["history_count"] == 7
    assert result["context_count"] == 2
```

运行：

```bash
python lesson_12.py
```

## 读懂结果

```text
history_count: 7
context_count: 2
```

输入六条历史，生成一条回复后共有七条；model_input 始终只有两条。这个例子仅包含普通问答，并未处理工具消息组。

### 代码抓住三处

1. `select_context` 选择本轮输入，但不修改 messages 历史。
2. 模拟模型节点根据 model_input 工作，新增回复仍写入 messages。
3. audit 在回复写入后统计数量，因此 history_count 比初始值多 1。

## 动手改一处

在最后一条用户消息之前，再插入一组用户问答，history_count 应变为 9，context_count 仍为 2。将计数断言同步更新。

## 最容易踩的坑

工具结果不能脱离对应的工具请求随意截取。若为这个图增加 checkpointer，model_input 也是 State 字段，可能同样被持久化；少发给模型不等于从存储中删除。

## 记住这一点

**完整历史负责留存，本轮上下文负责模型输入。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/add-memory)。

下一篇建议继续看：

- [Runtime Context：把运行依赖与状态分开](../13-runtime-context/index.html)
