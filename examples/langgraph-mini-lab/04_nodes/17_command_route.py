# 17｜Command 更新并跳转
# 顶层业务节点：4（不计 START / END）
# 流程：START -> choose -> [fast 或 normal] -> finish -> END
# 重点：Command(update=..., goto=...) 在节点内合并状态更新和路由
# 预期：fast: 加急处理 / normal: 普通处理
# 动手改：把 urgent 改成 False，观察路径和结果变化。
# 注意：不要再给 choose 加固定出边；固定边不会被 Command 自动取消。

from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

class State(TypedDict):
    urgent: bool
    route: str
    text: str

def choose(state: State) -> Command[Literal["fast", "normal"]]:
    target = "fast" if state["urgent"] else "normal"
    return Command(update={"route": target}, goto=target)

def fast(state: State) -> dict:
    return {"text": "加急处理"}

def normal(state: State) -> dict:
    return {"text": "普通处理"}

def finish(state: State) -> dict:
    return {"text": f"{state['route']}: {state['text']}"}

builder = StateGraph(State)
builder.add_node("choose", choose)
builder.add_node("fast", fast)
builder.add_node("normal", normal)
builder.add_node("finish", finish)
builder.add_edge(START, "choose")
builder.add_edge("fast", "finish")
builder.add_edge("normal", "finish")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    urgent = graph.invoke({"urgent": True})
    normal_result = graph.invoke({"urgent": False})
    print(urgent["text"])
    print(normal_result["text"])
    assert urgent["text"] == "fast: 加急处理"
    assert normal_result["text"] == "normal: 普通处理"
