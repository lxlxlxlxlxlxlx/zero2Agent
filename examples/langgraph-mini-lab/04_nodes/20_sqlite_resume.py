# 20｜SQLite 跨进程恢复
# 顶层业务节点：4（不计 START / END）
# 流程：START -> prepare -> approve(暂停) -> execute -> finish -> END
# 重点：SqliteSaver 写磁盘；先 start 退出程序，再 resume 恢复同一会话
# 预期：已保存暂停点: {'request': '发布草稿'} / 待执行: ('approve',) / 模拟发布完成。 / 待执行: ()
# 动手改：先 start，再单独执行 status，最后 resume；观察待执行节点。
# 注意：先安装 requirements-sqlite.txt；execute 只生成字符串，不执行真实发布。

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
        raise SystemExit("用法: python 04_nodes/20_sqlite_resume.py start|resume|status")
    main(sys.argv[1])
