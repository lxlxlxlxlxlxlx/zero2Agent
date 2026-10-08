# 08｜条件分支
# 顶层业务节点：3（不计 START / END）
# 流程：START -> check -> [allow 或 reject] -> END
# 重点：节点更新状态；路由函数返回标签；path_map 将标签映射到节点
# 预期：75: 通过 / 40: 不通过
# 动手改：把阈值 60 改成 80，重新预测输入 75 和 40 的结果。
# 注意：route 是边上的函数，不是 add_node 注册的业务节点。

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    score: int
    passed: bool
    result: str

def check(state: State) -> dict:
    return {"passed": state["score"] >= 60}

def route(state: State) -> str:
    return "yes" if state["passed"] else "no"

def allow(state: State) -> dict:
    return {"result": "通过"}

def reject(state: State) -> dict:
    return {"result": "不通过"}

builder = StateGraph(State)
builder.add_node("check", check)
builder.add_node("allow", allow)
builder.add_node("reject", reject)
builder.add_edge(START, "check")
builder.add_conditional_edges("check", route, {"yes": "allow", "no": "reject"})
builder.add_edge("allow", END)
builder.add_edge("reject", END)
graph = builder.compile()

if __name__ == "__main__":
    for score, expected in [(75, "通过"), (40, "不通过")]:
        result = graph.invoke({"score": score})
        print(f"{score}: {result['result']}")
        assert result["result"] == expected
