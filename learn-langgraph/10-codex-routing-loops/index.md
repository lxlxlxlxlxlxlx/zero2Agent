---
layout: default
title: "[codex] 条件路由、循环与 Command"
description: "用退出条件和显式路由控制图的下一步"
eyebrow: "LangGraph / 10"
---

# [codex] 条件路由、循环与 Command

草稿没达标时再写一次，紧急任务走快速通道，这些都需要决定下一步。难点在于把“更新了什么”和“接下来去哪”表达清楚，并确保循环最终能停下来。

## 运行准备

在自己新建的练习目录中运行以下命令；本页所有实验代码都已完整展开，可以直接复制保存，不需要下载源码或依赖原始资料目录。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "langgraph==1.2.12" "langchain-core>=1.0,<2.0" "pydantic>=2.7.4,<3.0"
```

建议 Python 3.11 或以上；fish 用户用 `source .venv/bin/activate.fish` 激活。已在前一篇创建环境的读者可以继续使用同一环境。核心版本用于复现实验，其余依赖是范围约束；主练习不需要模型 API Key。

## 条件边先分开更新和判断

实验 08 的 check 节点计算 `passed`，route 函数返回 `yes/no`，path_map 再映射到 allow/reject。route 是边上的函数，不是业务节点。

### 实验 08：条件分支 {#experiment-08}

将下面的完整代码保存为 `08_conditional_edges.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
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
```

运行：

```bash
python 08_conditional_edges.py
```

预期输出：

```text
75: 通过
40: 不通过
```

把条件判断放在路由函数里很直观，但不要用路由函数偷偷修改状态。节点提交数据更新，边选择后继，职责分开后才容易查看执行轨迹。

## 回边让一个节点重复执行

实验 09 的流程如下：

```mermaid
flowchart LR
    S["START"] --> W["write 生成草稿"]
    W --> C["check 检查长度"]
    C -->|"未达标"| W
    C -->|"达标"| F["finish 生成报告"]
    F --> E["END"]
```

### 实验 09：回边与退出条件 {#experiment-09}

将下面的完整代码保存为 `09_loop.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    attempts: int
    passed: bool
    report: str

def write(state: State) -> dict:
    return {"text": state["text"] + "好", "attempts": state["attempts"] + 1}

def check(state: State) -> dict:
    return {"passed": len(state["text"]) >= 2}

def route(state: State) -> str:
    return "finish" if state["passed"] else "write"

def finish(state: State) -> dict:
    return {"report": f"{state['text']}，尝试 {state['attempts']} 次"}

builder = StateGraph(State)
builder.add_node("write", write)
builder.add_node("check", check)
builder.add_node("finish", finish)
builder.add_edge(START, "write")
builder.add_edge("write", "check")
builder.add_conditional_edges("check", route, ["write", "finish"])
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"text": "", "attempts": 0}, {"recursion_limit": 20})
    print(result["report"])
    assert result["attempts"] == 2 and result["passed"]
```

运行：

```bash
python 09_loop.py
```

预期输出：

```text
好好，尝试 2 次
```

每次 write 追加一个“好”，两轮后通过长度检查。`attempts` 是业务尝试次数，`recursion_limit` 是图超步上限；两者不能互换，一轮业务操作可能经过多个超步。

原例为了隔离机制，只设长度条件和框架兜底。真实生成任务建议再加入业务次数上限，例如将实验 09 的 route 替换成：

```python
def route(state: State) -> str:
    if state["passed"] or state["attempts"] >= 3:
        return "finish"
    return "write"
```

同时修改 finish：未通过时返回失败原因，不能把“次数耗尽”包装成生成成功。耗时、Token 和工具调用预算需要各自记录，图的超步限制不能覆盖这些预算。

## Command：节点同时更新与跳转

当紧急程度既决定状态中的 route，又决定后继节点时，实验 17 用 Command 将这两个动作放在同一个返回值中：

### 实验 17：Command 更新并跳转 {#experiment-17}

将下面的完整代码保存为 `17_command_route.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
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
```

运行：

```bash
python 17_command_route.py
```

预期输出：

```text
fast: 加急处理
normal: 普通处理
```

`Command[Literal["fast", "normal"]]` 描述可能的跳转目标。不要再给 choose 添加普通固定出边：`goto` 不会自动撤销已注册的静态边，否则可能意外执行两条路径。

fast 和 normal 是互斥分支，所以分别连 finish。不能写 `add_edge(["fast", "normal"], "finish")` 等待两者都完成，因为每次只会执行其中一个。

## 怎么选择

| 场景 | 表达方式 | 重点 |
|---|---|---|
| 下一步永远一样 | `add_edge` | 固定依赖 |
| 依据已有状态选择后继 | `add_conditional_edges` | 路由标签和映射一致 |
| 更新状态时顺便决定后继 | `Command(update=..., goto=...)` | 避免重复的出边 |
| 返回某一步反复执行 | 回边配合条件 | 明确成功、失败和次数耗尽 |

这是本系列的设计建议，不是要求所有路由都改用 Command。

## 动手验证

实验 08 将阈值从 60 改为 80，75 应走拒绝路径。实验 09 将长度条件改为 3，write 应执行三次；再把条件改为永远不成立，确认运行会触发超步保护，而不是输出正常成功。实验 17 分别输入 True 和 False，确认每次只执行一个分支。

## 本页实验回顾

| 实验 | 已展开的内容 |
|---|---|
| 08 | 条件分支 |
| 09 | 回边与退出条件 |
| 17 | Command 更新并跳转 |

## 小结

- 路由决定后继，数据更新仍需要明确的节点返回值。
- 回边必须有可达的终止路径，兜底异常不等于业务成功。
- 互斥路径与必须全部完成的并行路径，用不同的汇合方式。

机制参考：[Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [[codex] 异步并行、汇合屏障与 Send](../11-codex-parallel-send/index.html)
