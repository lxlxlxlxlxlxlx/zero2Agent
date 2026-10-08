---
layout: default
title: "[codex] State、Context 与跨会话记忆"
description: "分清会话状态、运行依赖和跨线程记忆的生命周期"
eyebrow: "LangGraph / 09"
---

# [codex] State、Context 与跨会话记忆

同一个用户开了两个对话，希望昵称能延续，但不能让两个任务的中间结果串起来。如果把用户配置、消息历史和临时计数都塞进一个 State，这三个需求很容易互相干扰。

这一篇把数据按生命周期拆开：当前任务的数据放 State，本次运行的依赖放 Context，需要跨会话复用的资料通过 Store 管理。

## 运行准备

在自己新建的练习目录中运行以下命令；本页所有实验代码都已完整展开，可以直接复制保存，不需要下载源码或依赖原始资料目录。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "langgraph==1.2.12" "langchain-core>=1.0,<2.0" "pydantic>=2.7.4,<3.0"
```

建议 Python 3.11 或以上；fish 用户用 `source .venv/bin/activate.fish` 激活。已在前一篇创建环境的读者可以继续使用同一环境。核心版本用于复现实验，其余依赖是范围约束；主练习不需要模型 API Key。

## 先区分四个角色

| 角色 | 实验中的例子 | 保存和隔离方式 |
|---|---|---|
| State | 次数、报告、处理中的输入 | 节点读写；配合 checkpointer 保存 |
| Checkpointer | 线程 A 执行到哪里 | 按 `thread_id` 关联状态快照 |
| Runtime.context | 问候前缀、调用者 user_id | 调用时注入，不自动写进 State |
| Store | 用户昵称 | 按 namespace 与 key 管理，可跨 thread 访问 |

熟悉 Java 的读者可以把 Context 类比为一次请求显式传入的依赖，把 State 类比为流程中的 DTO；但它们没有 Spring 容器或数据库事务的隐含保证。

## 先看会话保留，再看运行依赖

实验 05 编译时传入 `InMemorySaver()`，用两条 thread 比较状态保留与隔离：

### 实验 05：会话状态与 thread_id {#experiment-05}

将下面的完整代码保存为 `05_checkpoint_threads.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
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
```

运行：

```bash
python 05_checkpoint_threads.py
```

预期输出：

```text
A: 1
A: 2
B: 1
```

第二次使用线程 A 时，只传 `label`，已有 `count` 会保留。若主动传入 `count=0`，你就在更新已有状态，结果也会变化。同一 `thread_id` 传一个新输入字典，是新一轮执行；人工中断的恢复另用 `Command(resume=...)`，见[第 13 篇](../13-codex-interrupt-persistence/index.html)。

实验 06 用 `StateGraph(State, context_schema=Context)` 声明上下文，并通过 `invoke(..., context=Context(prefix="Hello"))` 注入。节点通过 `runtime.context.prefix` 读取，返回状态里没有 `prefix`。恢复任务时仍应重新提供所需 context，不能期待它自动从检查点还原。

### 实验 06：运行时上下文 {#experiment-06}

将下面的完整代码保存为 `06_runtime_context.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
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
```

运行：

```bash
python 06_runtime_context.py
```

预期输出：

```text
Hello, 小林!
```

## 完整示例：换 thread，保留用户昵称

### 实验 13：跨会话记忆 {#experiment-13}

将下面的完整代码保存为 `13_store_memory.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

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
python 13_store_memory.py
```

预期输出：

```text
t1/u1: 你好，小林
t2/u1: 你好，小林
t3/u2: 你好，陌生人
```

第一次调用把小林写到 `("users", "u1")` 的 `profile` 中；第二次换到线程 t2，仍能按 u1 找到同一条资料。第三次使用 u2，没有对应记录，返回陌生人。

这里显式传 `remember_name=""` 表示本轮不写新昵称。若你复用同一 thread 却省略这个字段，旧 State 中的昵称可能仍在，remember 节点就可能重复写入。输入命令和持久状态有不同生命周期，生产实现应明确区分。

## 容易误判的边界

`InMemorySaver` 和 `InMemoryStore` 都只在当前进程存在。换两个 thread 得到相同昵称，只验证了同进程跨会话读取，不能据此宣称进程重启后记忆仍在。

namespace 也不是权限系统。本例的 user_id 是调用端提供的演示值；真实服务应从可信认证结果构造身份，并控制用户能访问的 thread 和 namespace。不要让请求参数随意指定其他人的身份。

Store 的这次实验只用 `put/get`，没有接向量检索，也没有把资料自动放入模型 Prompt。是否读取、筛选、发送给模型，仍由节点负责。

## 动手验证

先运行实验 05、06、13。将实验 13 第二次调用的 user_id 改为 u2，预期第二条答案变成陌生人；将 Context 的问候前缀改掉，确认无需修改状态定义。然后退出 Python，重新运行，观察内存存储重新开始。

## 本页实验回顾

| 实验 | 已展开的内容 |
|---|---|
| 05 | 会话状态与 thread_id |
| 06 | 运行时上下文 |
| 13 | 跨会话记忆 |

## 小结

- `thread_id` 标识流程状态，不等于用户身份。
- Context 注入本次运行所需依赖，Store 管跨会话资料。
- 是否落盘、是否有权限校验，要单独验证。

机制参考：[Memory](https://docs.langchain.com/oss/python/langgraph/add-memory)、[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)。

下一篇建议继续看：

- [[codex] 条件路由、循环与 Command](../10-codex-routing-loops/index.html)
