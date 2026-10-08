# 03｜消息按 ID 更新
# 顶层业务节点：2（不计 START / END）
# 流程：START -> draft -> revise -> END
# 重点：MessagesState 内置 add_messages；同 ID 更新，新 ID 追加
# 预期：[('human', '你好'), ('ai', '修订稿')]
# 动手改：把 revise 的 id 改为 answer-2，观察消息数从 2 变成 3。
# 注意：这里只手工构造消息，没有调用大模型。

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
