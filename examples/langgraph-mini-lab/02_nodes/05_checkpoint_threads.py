# 05｜会话状态与 thread_id
# 顶层业务节点：2（不计 START / END）
# 流程：START -> increment -> make_report -> END
# 重点：InMemorySaver、同一 thread 累积状态、不同 thread 隔离
# 预期：A: 1 / A: 2 / B: 1
# 动手改：第二次调用改用 config_b，预测 A 和 B 的次数。
# 注意：内存检查点不跨进程保存；再次 invoke(dict) 是新一轮，不是故障恢复。

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    label: str
    count: int
    report: str

def increment(state: State) -> dict:
    return {"count": state.get("count", 0) + 1}

def make_report(state: State) -> dict:
    return {"report": f"{state['label']}: {state['count']}"}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_node("make_report", make_report)
builder.add_edge(START, "increment")
builder.add_edge("increment", "make_report")
builder.add_edge("make_report", END)
graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    config_a = {"configurable": {"thread_id": "A"}}
    config_b = {"configurable": {"thread_id": "B"}}
    a1 = graph.invoke({"label": "A"}, config_a)
    a2 = graph.invoke({"label": "A"}, config_a)
    b1 = graph.invoke({"label": "B"}, config_b)
    for result in (a1, a2, b1):
        print(result["report"])
    snapshot = graph.get_state(config_a)
    assert (a1["count"], a2["count"], b1["count"]) == (1, 2, 1)
    assert snapshot.values["count"] == 2 and snapshot.next == ()
