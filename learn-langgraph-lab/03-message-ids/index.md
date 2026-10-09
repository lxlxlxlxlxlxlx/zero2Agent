---
layout: default
title: "消息 ID：追加一条还是修订一条"
description: "用 MessagesState 更新同一条消息"
eyebrow: "LangGraph 实验课 / 03"
---

# 消息 ID：追加一条还是修订一条

回答生成了初稿，又被修改为修订稿。聊天历史应该显示两条回答，还是同一条回答的新版本？这由消息标识和合并方式共同决定。

## 只看这个机制

**MessagesState 内置 add_messages，能按消息 ID 更新已有消息。** 相同 ID 表示同一条消息的新版本；新 ID 表示另一个消息。普通列表相加不具备这种身份语义。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_03.py`。导入、状态、节点和连线都在这个文件里。

```python
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph, START, END

def draft(state: MessagesState) -> dict:
    return {"messages": [AIMessage(content="初稿", id="answer-1")]}

def revise(state: MessagesState) -> dict:
    return {"messages": [AIMessage(content="修订稿", id="answer-1")]}

builder = StateGraph(MessagesState)
builder.add_node("draft", draft)
builder.add_node("revise", revise)
builder.add_edge(START, "draft")
builder.add_edge("draft", "revise")
builder.add_edge("revise", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"messages": [HumanMessage(content="你好", id="user-1")]})
    messages = result["messages"]
    print([(message.type, message.content) for message in messages])
    assert len(messages) == 2
    assert messages[-1].content == "修订稿"
```

运行：

```bash
python lesson_03.py
```

## 读懂结果

```text
[('human', '你好'), ('ai', '修订稿')]
```

最终只有一条用户消息和一条 AI 消息。两次节点执行都使用 answer-1，所以修订稿替换了初稿。这里手工构造 AIMessage，没有调用模型。

### 代码抓住三处

1. `MessagesState` 已定义 messages 字段及其合并规则，不必再写列表 reducer。
2. `draft` 与 `revise` 使用相同消息 ID，后一次内容覆盖同一消息。
3. 初始用户消息仍然保留；更新 AI 消息不会清空整段对话。

## 动手改一处

把 revise 中的 ID 改为 `answer-2`，应保留初稿和修订稿，消息总数从 2 变为 3；将长度断言同步改为 3。

## 最容易踩的坑

消息 id 用于更新消息，工具请求 id 与 tool_call_id 用于关联调用和结果。不要因为都叫 ID 就在两种用途之间混用。

## 记住这一点

**要修订同一对象，就保留它的标识。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [条件边：让状态决定下一步](../04-conditional-routing/index.html)
