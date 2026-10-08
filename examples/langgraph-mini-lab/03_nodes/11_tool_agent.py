# 11｜工具调用闭环（模拟模型）
# 顶层业务节点：3（不计 START / END）
# 流程：START -> model -> tools -> model -> finish -> END
# 重点：AIMessage.tool_calls、@tool、ToolNode、ToolMessage、条件路由
# 预期：答案: 7 / ['human', 'ai', 'tool', 'ai']
# 动手改：把模拟模型的工具参数 a=3,b=4 改成 a=10,b=20。
# 注意：模型决策被固定规则替代；工具是真执行。修改提问文本不会自动改变参数。

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

class State(MessagesState):
    answer: str

@tool
def add(a: int, b: int) -> int:
    """返回两个整数的和。"""
    return a + b

def model(state: State) -> dict:
    last = state["messages"][-1]
    if isinstance(last, ToolMessage):
        return {"messages": [AIMessage(content=f"答案: {last.content}")]}
    call = {"name": "add", "args": {"a": 3, "b": 4}, "id": "call-1", "type": "tool_call"}
    return {"messages": [AIMessage(content="", tool_calls=[call])]}

def finish(state: State) -> dict:
    return {"answer": state["messages"][-1].content}

builder = StateGraph(State)
builder.add_node("model", model)
builder.add_node("tools", ToolNode([add]))
builder.add_node("finish", finish)
builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition, {"tools": "tools", END: "finish"})
builder.add_edge("tools", "model")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"messages": [HumanMessage(content="计算 3 + 4")]},
                          {"recursion_limit": 10})
    messages = result["messages"]
    print(result["answer"])
    print([message.type for message in messages])
    assert result["answer"] == "答案: 7"
    assert messages[2].tool_call_id == messages[1].tool_calls[0]["id"]
    assert [message.type for message in messages] == ["human", "ai", "tool", "ai"]
