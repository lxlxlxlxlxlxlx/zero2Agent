---
layout: default
title: "幂等：提交后超时，重试会不会重复写入"
description: "用稳定业务键约束重复请求的结果"
eyebrow: "LangGraph 实验课 / 19"
---

# 幂等：提交后超时，重试会不会重复写入

数据库已经提交，只是响应没回来。调用方看到超时再执行一次，可能产生重复记录；成功返回与成功提交并不是同一个时刻。

## 只看这个机制

**幂等依赖稳定业务键与接收方的去重规则。** 本例用主键约束加 ON CONFLICT DO NOTHING，第一次提交后主动抛超时，第二次沿用同一个 job-1。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_19.py`。导入、状态、节点和连线都在这个文件里。

```python
import sqlite3
from itertools import count
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    task_id: str
    rows: int

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

policy = RetryPolicy(max_attempts=2, retry_on=TimeoutError,
                     initial_interval=0, jitter=False)
builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("save", save, retry_policy=policy)
builder.add_node("count_rows", count_rows)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "save")
builder.add_edge("save", "count_rows")
builder.add_edge("count_rows", END)
graph = builder.compile()

if __name__ == "__main__":
    try:
        result = graph.invoke({"task_id": "job-1"})
        print(f"数据库记录: {result['rows']}")
        assert result["rows"] == 1
    finally:
        connection.close()
```

运行：

```bash
python lesson_19.py
```

## 读懂结果

```text
写入尝试: 1
写入尝试: 2
数据库记录: 1
```

尝试两次，数据库仍只有一条记录。第二次插入命中已有主键，变成无操作；保护结果的是存储约束，不是异常本身。

### 代码抓住三处

1. job-1 在两次执行间保持不变，数据库用主键识别同一业务操作。
2. 第一次已经 commit，再抛超时，模拟“成功了但调用方不知道”。
3. 第二次遇到主键冲突不新增行，因此执行次数为 2，记录数量为 1。

## 动手改一处

去掉 ON CONFLICT 子句并保留主键，第二次插入应出现唯一键冲突。不要把该冲突当作临时网络错误无限重试。

## 最容易踩的坑

每次重试重新生成随机业务 ID 会绕过去重。真实系统还需检查同键不同参数；内存 SQLite 不跨进程保存，check_same_thread=False 也不保证任意并发写入安全。

## 记住这一点

**先确定同一业务操作的身份，再允许它被重复尝试。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/persistence)。

下一篇建议继续看：

- [子图：隐藏内部步骤，保留数据接口](../20-subgraphs/index.html)
