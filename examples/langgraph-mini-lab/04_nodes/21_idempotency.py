# 21｜重试时避免重复写入
# 顶层业务节点：4（不计 START / END）
# 流程：START -> prepare -> save(提交后超时并重试) -> count_rows -> finish -> END
# 重点：同一业务 id + 数据库唯一约束，让重复尝试只产生一条记录
# 预期：写入尝试: 1 / 写入尝试: 2 / 数据库记录: 1
# 动手改：去掉 ON CONFLICT 子句，观察第二次尝试出现唯一键冲突。
# 注意：演示单流程顺序执行；数据库为内存库；不代表外部 API 自动具有幂等性。

import sqlite3
from itertools import count
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    task_id: str
    rows: int
    report: str

# 节点可能由执行器线程调用；本例图内没有并行数据库操作。
connection = sqlite3.connect(":memory:", check_same_thread=False)
connection.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
attempts = count(1)

def prepare(state: State) -> dict:
    task_id = state["task_id"].strip()
    if not task_id:
        raise ValueError("task_id 不能为空")
    return {"task_id": task_id}

def save(state: State) -> dict:
    connection.execute("INSERT INTO jobs(id) VALUES (?) ON CONFLICT(id) DO NOTHING",
                       (state["task_id"],))
    connection.commit()  # 已经写成功，但模拟返回途中超时。
    attempt = next(attempts)
    print(f"写入尝试: {attempt}")
    if attempt == 1:
        raise TimeoutError("提交后超时")
    return {}

def count_rows(state: State) -> dict:
    return {"rows": connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]}

def finish(state: State) -> dict:
    return {"report": f"数据库记录: {state['rows']}"}

policy = RetryPolicy(max_attempts=2, retry_on=TimeoutError,
                     initial_interval=0, jitter=False)
builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("save", save, retry_policy=policy)
builder.add_node("count_rows", count_rows)
builder.add_node("finish", finish)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "save")
builder.add_edge("save", "count_rows")
builder.add_edge("count_rows", "finish")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    try:
        result = graph.invoke({"task_id": "job-1"})
        print(result["report"])
        assert result["rows"] == 1
    finally:
        connection.close()
