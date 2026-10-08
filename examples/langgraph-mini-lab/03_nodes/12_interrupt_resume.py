# 12｜人工审批与恢复
# 顶层业务节点：3（不计 START / END）
# 流程：START -> prepare -> approve（暂停）-> finish -> END
# 重点：interrupt、Command(resume=...)、checkpointer、同一个 thread_id
# 预期：进入审批 / 暂停: {'request': '发布草稿'} / 进入审批 / 已批准
# 动手改：把 Command(resume=True) 改成 False，结果应为已拒绝。
# 注意：恢复会从 approve 节点开头重跑，所以进入审批会打印两次。

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

class State(TypedDict):
    request: str
    approved: bool
    result: str

def prepare(state: State) -> dict:
    return {"request": state["request"].strip()}

def approve(state: State) -> dict:
    print("进入审批")
    approved = interrupt({"request": state["request"]})
    if not isinstance(approved, bool):
        raise ValueError("审批结果必须是 True 或 False")
    return {"approved": approved}

def finish(state: State) -> dict:
    return {"result": "已批准" if state["approved"] else "已拒绝"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("approve", approve)
builder.add_node("finish", finish)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "approve")
builder.add_edge("approve", "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "approval-1"}}
    paused = graph.invoke({"request": " 发布草稿 "}, config)
    print("暂停:", paused["__interrupt__"][0].value)
    assert graph.get_state(config).next == ("approve",)
    result = graph.invoke(Command(resume=True), config)
    print(result["result"])
    assert result["approved"] is True
    assert graph.get_state(config).next == ()
