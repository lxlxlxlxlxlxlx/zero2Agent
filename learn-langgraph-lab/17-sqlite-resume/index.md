---
layout: default
title: "SQLite：退出程序后恢复暂停任务"
description: "用四次独立进程验证检查点落盘"
eyebrow: "LangGraph 实验课 / 17"
---

# SQLite：退出程序后恢复暂停任务

内存里的暂停任务在进程退出后就消失。要证明任务真的可恢复，应先让程序结束，再启动另一个进程继续同一任务。

## 只看这个机制

**SqliteSaver 将检查点写入本地数据库。** 数据库文件、thread_id 和兼容的图定义共同定位暂停位置；连接关闭前完成本轮读写。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

本课额外安装：

```bash
python -m pip install "langgraph-checkpoint-sqlite==3.1.1"
```

将下面代码保存为 `lesson_17.py`。导入、状态、节点和连线都在这个文件里。

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
    return {"result": "模拟发布完成。" if state["approved"] else "已取消。"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("approve", approve)
builder.add_node("execute", execute)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "approve")
builder.add_edge("approve", "execute")
builder.add_edge("execute", END)

def main(mode: str) -> None:
    data_dir = Path(os.environ.get("LANGGRAPH_LAB_DATA_DIR", ".runtime"))
    data_dir.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": "sqlite-demo"}}
    with SqliteSaver.from_conn_string(str(data_dir / "lesson17.sqlite")) as saver:
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
        raise SystemExit("用法: python lesson_17.py start|resume|status")
    main(sys.argv[1])
```

运行：

```bash
python lesson_17.py start
python lesson_17.py status
python lesson_17.py resume
python lesson_17.py status
```

## 读懂结果

```text
已保存暂停点: {'request': '发布草稿'}
待执行: ('approve',)
模拟发布完成。
待执行: ()
```

start 保存审批暂停点；status 只查看 next；resume 在新进程提交批准结果；最后 status 显示没有待执行节点。发布只生成字符串，不执行外部操作。

数据库默认在当前目录的 `.runtime/lesson17.sqlite`。四条命令要在同一目录分别运行；每次 Python 退出后，下一次才能证明跨进程恢复。

### 代码抓住三处

1. `from_conn_string` 打开同一个数据库，用 with 管理连接关闭。
2. start 提交新任务，resume 提交恢复值，status 仅查看快照。
3. 四次命令启动四个 Python 进程，连接和内存都重建，数据库保留检查点。

## 动手改一处

在 start 后退出终端，再回到同一练习目录并激活虚拟环境。先再次运行 start，它应拒绝覆盖已有暂停任务；随后运行 status 和 resume，完成这一轮。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

换工作目录可能创建另一个空数据库，不能据此判断原任务丢失。重命名暂停节点或不兼容地改 State 也可能破坏恢复；检查点不自动保证外部副作用恰好一次。

## 记住这一点

**跨进程验证才能证明落盘恢复，内存重跑不能替代它。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/persistence)。

下一篇建议继续看：

- [RetryPolicy：只重试可恢复的错误](../18-retry-policy/index.html)
