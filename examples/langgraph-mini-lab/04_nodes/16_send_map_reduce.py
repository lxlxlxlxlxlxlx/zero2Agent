# 16｜Send 动态分发
# 顶层业务节点：4（不计 START / END）
# 流程：START -> prepare -> square(每项一个任务) -> collect -> make_report -> END
# 重点：节点定义数固定，Send 任务数动态；worker 接收自己的小状态
# 预期：平方和: 29 / 空任务: 0
# 动手改：把 numbers 改为 [1, 2, 3, 4]，预测总和与 square 执行次数。
# 注意：空列表单独路由到 collect；不依赖并行结果的先后顺序。

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    numbers: list[int]
    tasks: list[int]
    squares: Annotated[list[int], operator.add]
    total: int
    report: str

class WorkerState(TypedDict):
    number: int

def prepare(state: State) -> dict:
    return {"tasks": state["numbers"]}

def dispatch(state: State):
    if not state["tasks"]:
        return "collect"
    return [Send("square", {"number": n}) for n in state["tasks"]]

def square(state: WorkerState) -> dict:
    return {"squares": [state["number"] ** 2]}

def collect(state: State) -> dict:
    return {"total": sum(state["squares"])}

def make_report(state: State) -> dict:
    return {"report": f"平方和: {state['total']}"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("square", square)
builder.add_node("collect", collect)
builder.add_node("make_report", make_report)
builder.add_edge(START, "prepare")
builder.add_conditional_edges("prepare", dispatch, ["square", "collect"])
builder.add_edge("square", "collect")
builder.add_edge("collect", "make_report")
builder.add_edge("make_report", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"numbers": [2, 3, 4], "squares": []})
    empty = graph.invoke({"numbers": [], "squares": []})
    print(result["report"])
    print("空任务:", empty["total"])
    assert sorted(result["squares"]) == [4, 9, 16]
    assert result["total"] == 29 and empty["total"] == 0
