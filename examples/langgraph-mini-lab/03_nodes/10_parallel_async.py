# 10｜异步并行与等待汇总
# 顶层业务节点：3（不计 START / END）
# 流程：START -> [left 与 right 并行] -> collect -> END
# 重点：async/await、ainvoke/astream、共享字段 reducer、列表形式汇合边
# 预期：ainvoke: 13 / astream: 13
# 动手改：将 right 返回的数字 8 改成 10，预测 total。
# 注意：异步用于等待 I/O；不按并行节点完成顺序写断言；两次调用是两轮执行。

import asyncio
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    values: Annotated[list[int], operator.add]
    total: int

async def left(state: State) -> dict:
    await asyncio.sleep(0.02)
    return {"values": [5]}

async def right(state: State) -> dict:
    await asyncio.sleep(0.01)
    return {"values": [8]}

def collect(state: State) -> dict:
    return {"total": sum(state["values"])}

builder = StateGraph(State)
builder.add_node("left", left)
builder.add_node("right", right)
builder.add_node("collect", collect)
builder.add_edge(START, "left")
builder.add_edge(START, "right")
builder.add_edge(["left", "right"], "collect")
builder.add_edge("collect", END)
graph = builder.compile()

async def main() -> None:
    result = await graph.ainvoke({"values": []})
    print("ainvoke:", result["total"])
    snapshots = []
    async for snapshot in graph.astream({"values": []}, stream_mode="values"):
        snapshots.append(snapshot)
    print("astream:", snapshots[-1]["total"])
    assert sorted(result["values"]) == [5, 8]
    assert result["total"] == snapshots[-1]["total"] == 13

if __name__ == "__main__":
    asyncio.run(main())
