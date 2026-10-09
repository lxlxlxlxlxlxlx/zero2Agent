---
layout: default
title: "Store：跨会话读取同一份用户资料"
description: "通过命名空间与 key 组织长期资料"
eyebrow: "LangGraph 实验课 / 15"
---

# Store：跨会话读取同一份用户资料

用户在新会话里希望系统还记得昵称，但旧会话的处理中间值不该一起带过去。跨会话资料需要独立于某条 thread 的存储。

## 只看这个机制

**Store 按 namespace 与 key 读写应用数据，Checkpointer 保存某条 thread 的执行状态。** 例子用 users/user_id 作为命名空间，用 profile 作为 key。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_15.py`。导入、状态、节点和连线都在这个文件里。

```python
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
```

运行：

```bash
python lesson_15.py
```

## 读懂结果

```text
t1/u1: 你好，小林
t2/u1: 你好，小林
t3/u2: 你好，陌生人
```

t1 给 u1 写入昵称；换成 t2 仍能按 u1 读取。u2 没有资料，返回陌生人。这只验证同进程跨会话读写。

### 代码抓住三处

1. `runtime.context` 提供 user_id，线程 ID 与用户 ID 分别承担不同职责。
2. `store.put(namespace, "profile", ...)` 写资料，get 使用相同位置读取。
3. 新线程不会继承旧线程状态，但可以主动按同一用户读取 Store。

## 动手改一处

将第二次调用的 user_id 改为 u2，第二条回答应变为“你好，陌生人”。保留不同用户的对照。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

InMemoryStore 不跨进程保留，namespace 也不是身份认证。本轮不写昵称时显式传空字符串，避免复用 thread 时旧 remember_name 残留又触发写入。

## 记住这一点

**用户资料按用户组织，任务状态按会话组织。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/add-memory)。

下一篇建议继续看：

- [Interrupt：等待审批，再继续执行](../16-interrupt-resume/index.html)
