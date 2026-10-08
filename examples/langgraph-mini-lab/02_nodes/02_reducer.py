# 02｜覆盖与追加的区别
# 顶层业务节点：2（不计 START / END）
# 流程：START -> first -> second -> END
# 重点：Annotated[list[str], operator.add] 为一个字段设置 reducer
# 预期：latest: B / history: ['A', 'B']
# 动手改：把 history 改成 list[str]，预测输出；记得同步修改断言。
# 注意：追加字段只返回新增项；返回旧列表 + 新项会重复累积。

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    latest: str
    history: Annotated[list[str], operator.add]

def first(state: State) -> dict:
    return {"latest": "A", "history": ["A"]}

def second(state: State) -> dict:
    return {"latest": "B", "history": ["B"]}

builder = StateGraph(State)
builder.add_node("first", first)
builder.add_node("second", second)
builder.add_edge(START, "first")
builder.add_edge("first", "second")
builder.add_edge("second", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"latest": "", "history": []})
    print("latest:", result["latest"])
    print("history:", result["history"])
    assert result["latest"] == "B"
    assert result["history"] == ["A", "B"]
