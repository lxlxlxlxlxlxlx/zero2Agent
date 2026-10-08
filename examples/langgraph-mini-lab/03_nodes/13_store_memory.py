# 13｜跨会话记忆
# 顶层业务节点：3（不计 START / END）
# 流程：START -> remember -> recall -> reply -> END
# 重点：Store 用 namespace + key 存值；不同 thread 可读取同一用户记忆
# 预期：t1/u1: 你好，小林 / t2/u1: 你好，小林 / t3/u2: 你好，陌生人
# 动手改：把第二次调用的 user_id 改成 u2，结果应为你好，陌生人。
# 注意：InMemoryStore 仅在当前进程存活；namespace 隔离不是身份认证。

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore

class Context(TypedDict):
    user_id: str

class State(TypedDict):
    remember_name: str
    name: str
    answer: str

def remember(state: State, runtime: Runtime[Context]) -> dict:
    if state.get("remember_name"):
        namespace = ("users", runtime.context["user_id"])
        runtime.store.put(namespace, "profile", {"name": state["remember_name"]})
    return {}

def recall(state: State, runtime: Runtime[Context]) -> dict:
    namespace = ("users", runtime.context["user_id"])
    item = runtime.store.get(namespace, "profile")
    return {"name": item.value["name"] if item else "陌生人"}

def reply(state: State) -> dict:
    return {"answer": f"你好，{state['name']}"}

builder = StateGraph(State, context_schema=Context)
builder.add_node("remember", remember)
builder.add_node("recall", recall)
builder.add_node("reply", reply)
builder.add_edge(START, "remember")
builder.add_edge("remember", "recall")
builder.add_edge("recall", "reply")
builder.add_edge("reply", END)
graph = builder.compile(checkpointer=InMemorySaver(), store=InMemoryStore())

if __name__ == "__main__":
    cases = [("t1", "u1", "小林"), ("t2", "u1", ""), ("t3", "u2", "")]
    answers = []
    for thread_id, user_id, name in cases:
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke({"remember_name": name}, config,
                              context={"user_id": user_id})
        answers.append(result["answer"])
        print(f"{thread_id}/{user_id}: {result['answer']}")
    assert answers == ["你好，小林", "你好，小林", "你好，陌生人"]
