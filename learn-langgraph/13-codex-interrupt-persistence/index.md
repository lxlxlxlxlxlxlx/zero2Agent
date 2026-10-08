---
layout: default
title: "[codex] 人工审批与跨进程恢复"
description: "从内存中断到 SQLite 保存与恢复暂停任务"
eyebrow: "LangGraph / 13"
---

# [codex] 人工审批与跨进程恢复

发布草稿前要等人工确认，审批可能隔几个小时才回来，服务期间还可能重启。把一个函数阻塞在那里等输入，无法解决这种任务恢复。我们需要保存执行位置，再用同一个任务标识继续。

## 运行准备

在自己新建的练习目录中运行以下命令；本页所有实验代码都已完整展开，可以直接复制保存，不需要下载源码或依赖原始资料目录。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "langgraph==1.2.12" "langchain-core>=1.0,<2.0" "pydantic>=2.7.4,<3.0"
```

建议 Python 3.11 或以上；fish 用户用 `source .venv/bin/activate.fish` 激活。已在前一篇创建环境的读者可以继续使用同一环境。核心版本用于复现实验，其余依赖是范围约束；主练习不需要模型 API Key。

## 中断需要哪些条件

`interrupt()` 提交待审批数据，checkpointer 保存图状态，`thread_id` 找回对应任务。恢复时传 `Command(resume=...)`，该值会成为中断调用的返回结果。

```mermaid
flowchart TB
    P["prepare 准备草稿"] --> A["approve 发起中断"]
    A --> C["保存检查点"]
    C --> U["外部审批"]
    U -->|"相同 thread_id 与 resume 值"| R["重入 approve"]
    R --> F["finish 生成结果"]
```

这是运行生命周期图；外部审批不是图里额外注册的业务节点。

## 先验证内存中的暂停与继续

### 实验 12：人工审批与恢复 {#experiment-12}

将下面的完整代码保存为 `12_interrupt_resume.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

class State(TypedDict):
    request: str
    approved: bool
    result: str

def prepare(state: State) -> dict:
    return {"request": state["request"].strip()}

def approve(state: State) -> dict:
    print("进入审批")
    approved = interrupt({"request": state["request"]})
    if not isinstance(approved, bool):
        raise ValueError("审批结果必须是 True 或 False")
    return {"approved": approved}

def finish(state: State) -> dict:
    return {"result": "已批准" if state["approved"] else "已拒绝"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("approve", approve)
builder.add_node("finish", finish)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "approve")
builder.add_edge("approve", "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "approval-1"}}
    paused = graph.invoke({"request": " 发布草稿 "}, config)
    print("暂停:", paused["__interrupt__"][0].value)
    assert graph.get_state(config).next == ("approve",)
    result = graph.invoke(Command(resume=True), config)
    print(result["result"])
    assert result["approved"] is True
    assert graph.get_state(config).next == ()
```

运行：

```bash
python 12_interrupt_resume.py
```

预期输出：

```text
进入审批
暂停: {'request': '发布草稿'}
进入审批
已批准
```

你会看到“进入审批”打印两次。恢复从 approve 节点开头重新执行，而不是从 Python 调用栈里原地接着往下走。把扣款、发送通知等副作用写在 interrupt 前面，重入时就可能重复发生。

示例检查审批结果必须是 bool；字符串 `"False"` 不是合法的拒绝值。不要用一个宽泛的 try/except 把 interrupt 的控制信号吞掉，也不要随意改变同一节点里多个 interrupt 的调用顺序。

## 把内存保存换成 SQLite

实验 20 将 saver 换成 `SqliteSaver`，还增加 execute 节点。先安装 SQLite 检查点扩展：

```bash
python -m pip install "langgraph-checkpoint-sqlite==3.1.1"
```

所有调用都在连接的 with 生命周期内进行，完整代码如下：

### 实验 20：SQLite 跨进程恢复 {#experiment-20}

将下面的完整代码保存为 `20_sqlite_resume.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
import os
import sys
from pathlib import Path
from typing import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

class State(TypedDict):
    request: str
    approved: bool
    result: str

def prepare(state: State) -> dict:
    return {"request": state["request"].strip()}

def approve(state: State) -> dict:
    approved = interrupt({"request": state["request"]})
    if not isinstance(approved, bool):
        raise ValueError("审批结果必须是 True 或 False")
    return {"approved": approved}

def execute(state: State) -> dict:
    return {"result": "模拟发布完成" if state["approved"] else "已取消"}

def finish(state: State) -> dict:
    return {"result": state["result"] + "。"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("approve", approve)
builder.add_node("execute", execute)
builder.add_node("finish", finish)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "approve")
builder.add_edge("approve", "execute")
builder.add_edge("execute", "finish")
builder.add_edge("finish", END)

def main(mode: str) -> None:
    data_dir = Path(os.environ.get("LANGGRAPH_LAB_DATA_DIR", ".runtime"))
    data_dir.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": "sqlite-demo"}}
    with SqliteSaver.from_conn_string(str(data_dir / "lesson20.sqlite")) as saver:
        graph = builder.compile(checkpointer=saver)
        snapshot = graph.get_state(config)
        if mode == "start":
            if snapshot.next:
                raise SystemExit("已有暂停任务，请先运行 resume。")
            paused = graph.invoke({"request": " 发布草稿 "}, config)
            print("已保存暂停点:", paused["__interrupt__"][0].value)
        elif mode == "resume":
            if not snapshot.next:
                raise SystemExit("没有暂停任务，请先运行 start。")
            result = graph.invoke(Command(resume=True), config)
            print(result["result"])
            assert result["result"] == "模拟发布完成。"
        else:
            print("待执行:", snapshot.next)

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"start", "resume", "status"}:
        raise SystemExit("用法: python 20_sqlite_resume.py start|resume|status")
    main(sys.argv[1])
```

在同一目录分别执行以下命令，每条命令都会启动一个新的 Python 进程：

```bash
python 20_sqlite_resume.py start
python 20_sqlite_resume.py status
python 20_sqlite_resume.py resume
python 20_sqlite_resume.py status
```

预期输出：

```text
已保存暂停点: {'request': '发布草稿'}
待执行: ('approve',)
模拟发布完成。
待执行: ()
```

预期先看到 `待执行: ('approve',)`，恢复后看到 `模拟发布完成。` 和 `待执行: ()`。这里的发布只是字符串，不会发布网站或发送任何消息。

手工数据库位于当前工作目录的 `.runtime/lesson20.sqlite`。同一数据库、同一 thread_id、兼容的图定义缺一不可；换目录导致创建空数据库时，不能把“找不到暂停任务”理解为恢复成功。

## 三种调用不要混淆

| 调用 | 本系列中的含义 |
|---|---|
| `invoke({...}, config)` | 提供本轮新输入，已有 thread 状态可能参与合并 |
| `invoke(Command(resume=True), config)` | 给当前人工中断传入批准结果 |
| `get_state(config)` | 查看已保存状态和 next，不推进业务节点 |

异常失败后的继续执行是另一类场景，不能把所有恢复都写成 `Command(resume=True)`。发布带长生命周期任务的图时，还要考虑节点重命名、删除和 State 结构变化对旧检查点的兼容影响。

`next == ()` 表示当前快照没有待执行节点；若业务返回的是“已拒绝”或失败结果，也可能没有待执行节点，因此仍需检查业务结果。

## 动手验证

将实验 12 的 resume 改为 False，确认得到已拒绝。实验 20 在 start 后先退出终端，再在同一实验目录运行 status 和 resume；重复 start 应拒绝覆盖暂停任务。不要通过删除数据库绕过未审批任务。

## 本页实验回顾

| 实验 | 已展开的内容 |
|---|---|
| 12 | 人工审批与恢复 |
| 20 | SQLite 跨进程恢复 |

## 小结

- 人工审批恢复依赖保存位置和任务标识，不能靠进程内变量。
- 中断节点会重入，副作用必须另有保护。
- 执行结束和业务通过是两种验收证据。

机制参考：[Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)、[Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)。

下一篇建议继续看：

- [[codex] 重试策略与业务幂等](../14-codex-retry-idempotency/index.html)
