# 09｜回边与退出条件
# 顶层业务节点：3（不计 START / END）
# 流程：START -> write -> check -> [write 或 finish] -> END
# 重点：同一节点可执行多次；业务条件退出；recursion_limit 作为兜底
# 预期：好好，尝试 2 次
# 动手改：把长度阈值从 2 改成 3，预测 write 执行几次。
# 注意：recursion_limit 是图超步数上限，不是业务尝试次数，也不是 Python 递归深度。

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    attempts: int
    passed: bool
    report: str

def write(state: State) -> dict:
    return {"text": state["text"] + "好", "attempts": state["attempts"] + 1}

def check(state: State) -> dict:
    return {"passed": len(state["text"]) >= 2}

def route(state: State) -> str:
    return "finish" if state["passed"] else "write"

def finish(state: State) -> dict:
    return {"report": f"{state['text']}，尝试 {state['attempts']} 次"}

builder = StateGraph(State)
builder.add_node("write", write)
builder.add_node("check", check)
builder.add_node("finish", finish)
builder.add_edge(START, "write")
builder.add_edge("write", "check")
builder.add_conditional_edges("check", route, ["write", "finish"])
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"text": "", "attempts": 0}, {"recursion_limit": 20})
    print(result["report"])
    assert result["attempts"] == 2 and result["passed"]
