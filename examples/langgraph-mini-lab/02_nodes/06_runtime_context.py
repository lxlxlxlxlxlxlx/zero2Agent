# 06｜运行时上下文
# 顶层业务节点：2（不计 START / END）
# 流程：START -> greet -> finish -> END
# 重点：State 是过程数据；Runtime.context 传本轮运行依赖或配置
# 预期：Hello, 小林!
# 动手改：把 context 中的 prefix 改成 Welcome，状态定义无需改变。
# 注意：context 不会自动成为检查点中的 State；恢复时需要重新提供所需 context。

from dataclasses import dataclass
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime

@dataclass
class Context:
    prefix: str

class State(TypedDict):
    name: str
    text: str

def greet(state: State, runtime: Runtime[Context]) -> dict:
    return {"text": f"{runtime.context.prefix}, {state['name']}"}

def finish(state: State) -> dict:
    return {"text": state["text"] + "!"}

builder = StateGraph(State, context_schema=Context)
builder.add_node("greet", greet)
builder.add_node("finish", finish)
builder.add_edge(START, "greet")
builder.add_edge("greet", "finish")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"name": "小林"}, context=Context(prefix="Hello"))
    print(result["text"])
    assert result["text"] == "Hello, 小林!"
    assert "prefix" not in result
