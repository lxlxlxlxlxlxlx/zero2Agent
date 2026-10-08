# 04｜节点更新与完整状态流
# 顶层业务节点：2（不计 START / END）
# 流程：START -> increment -> double -> END
# 重点：stream_mode="updates" 与 stream_mode="values" 的区别
# 预期：updates: [{'increment': {'n': 2}}, {'double': {'n': 4}}] / values: [{'n': 1}, {'n': 2}, {'n': 4}]
# 动手改：先预测两个模式各输出几次，再把初始 n 改成 3。
# 注意：下面调用 stream 两次，就是独立执行两遍；不是重复读取同一次执行。

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    n: int

def increment(state: State) -> dict:
    return {"n": state["n"] + 1}

def double(state: State) -> dict:
    return {"n": state["n"] * 2}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_node("double", double)
builder.add_edge(START, "increment")
builder.add_edge("increment", "double")
builder.add_edge("double", END)
graph = builder.compile()

if __name__ == "__main__":
    updates = list(graph.stream({"n": 1}, stream_mode="updates"))
    values = list(graph.stream({"n": 1}, stream_mode="values"))
    print("updates:", updates)
    print("values:", values)
    assert updates == [{"increment": {"n": 2}}, {"double": {"n": 4}}]
    assert values == [{"n": 1}, {"n": 2}, {"n": 4}]
