# 07｜节点自动重试
# 顶层业务节点：2（不计 START / END）
# 流程：START -> fetch -> finish -> END
# 重点：RetryPolicy 只重试指定异常；max_attempts 包含首次执行
# 预期：尝试 1 / 尝试 2 / 结果: 7
# 动手改：把 max_attempts 改成 1，观察首次 TimeoutError 直接向外抛出。
# 注意：attempts 仅模拟外部服务先失败后成功，不是跨进程可靠计数。

from itertools import count
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    value: int
    report: str

attempts = count(1)

def fetch(state: State) -> dict:
    attempt = next(attempts)
    print(f"尝试 {attempt}")
    if attempt == 1:
        raise TimeoutError("模拟第一次调用超时")
    return {"value": 7}

def finish(state: State) -> dict:
    return {"report": f"结果: {state['value']}"}

policy = RetryPolicy(
    max_attempts=2, retry_on=TimeoutError, initial_interval=0, jitter=False
)
builder = StateGraph(State)
builder.add_node("fetch", fetch, retry_policy=policy)
builder.add_node("finish", finish)
builder.add_edge(START, "fetch")
builder.add_edge("fetch", "finish")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"value": 0})
    print(result["report"])
    assert result["value"] == 7
