# 18｜子图封装与共享字段
# 顶层业务节点：4（不计 START / END）
# 流程：START -> normalize -> worker(子图) -> format_report -> finish -> END
# 重点：编译后的子图可作为父图节点；父子图通过共享字段衔接
# 预期：结果: 18，完成
# 动手改：把子图中的乘 2 改成乘 3，父图连线不用修改。
# 注意：这里是顶层 4 节点；worker 内部另有 square、double 两个节点。

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class ChildState(TypedDict):
    x: int
    squared: int
    result: int

def square(state: ChildState) -> dict:
    return {"squared": state["x"] ** 2}

def double(state: ChildState) -> dict:
    return {"result": state["squared"] * 2}

child_builder = StateGraph(ChildState)
child_builder.add_node("square", square)
child_builder.add_node("double", double)
child_builder.add_edge(START, "square")
child_builder.add_edge("square", "double")
child_builder.add_edge("double", END)
child = child_builder.compile()

class State(TypedDict):
    x: int
    result: int
    report: str

def normalize(state: State) -> dict:
    return {"x": abs(state["x"])}

def format_report(state: State) -> dict:
    return {"report": f"结果: {state['result']}"}

def finish(state: State) -> dict:
    return {"report": state["report"] + "，完成"}

builder = StateGraph(State)
builder.add_node("normalize", normalize)
builder.add_node("worker", child)
builder.add_node("format_report", format_report)
builder.add_node("finish", finish)
builder.add_edge(START, "normalize")
builder.add_edge("normalize", "worker")
builder.add_edge("worker", "format_report")
builder.add_edge("format_report", "finish")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"x": -3})
    print(result["report"])
    assert result["result"] == 18
    assert "squared" not in result
