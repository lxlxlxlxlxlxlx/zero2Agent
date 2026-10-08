# 14｜保存历史不等于全部发送给模型
# 顶层业务节点：3（不计 START / END）
# 流程：START -> select_context -> mock_model -> audit -> END
# 重点：将保留的 messages 与本轮 model_input 分开
# 预期：history_count: 7 / context_count: 2
# 动手改：给历史增加一组普通问答，预测 history_count 与 context_count。
# 注意：本例只有系统消息和普通问答；工具消息必须成对处理，不能随意这样截取。

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
