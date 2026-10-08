# 22｜真实模型工具闭环（选学；顶层 3 节点）
# 流程：START -> call_model -> tools -> call_model -> finish -> END
# 重点：将第 11 课固定的模型逻辑，替换为 bind_tools + invoke。
# 前提：安装 requirements-llm.txt；配置 LLM_MODEL；服务支持工具调用。
# 默认请求本机 127.0.0.1:8080，不会自动启动或下载模型。
# 输出不固定；更换远程地址可能产生调用费用。本例不纳入一键自测。
import os
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

class State(MessagesState):
    answer: str

@tool
def add(a: int, b: int) -> int:
    """返回两个整数的和。"""
    return a + b

def call_model(state: State) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

def finish(state: State) -> dict:
    return {"answer": str(state["messages"][-1].content)}

builder = StateGraph(State)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode([add]))
builder.add_node("finish", finish)
builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", tools_condition, {"tools": "tools", END: "finish"})
builder.add_edge("tools", "call_model")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    model_name = os.environ.get("LLM_MODEL")
    if not model_name:
        raise SystemExit("请先设置 LLM_MODEL，使用服务实际提供的模型名。")
    llm = ChatOpenAI(
        model=model_name,
        base_url=os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8080/v1"),
        api_key=os.environ.get("LLM_API_KEY", "local-not-used"),
        timeout=30,
        max_retries=0,
    ).bind_tools([add])
    result = graph.invoke(
        {"messages": [HumanMessage(content="请调用 add 工具计算 3 + 4，然后回答结果。")]},
        {"recursion_limit": 10},
    )
    print(result["answer"])
    print("消息轨迹:", [message.type for message in result["messages"]])
