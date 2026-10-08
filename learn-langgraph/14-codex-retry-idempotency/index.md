---
layout: default
title: "[codex] 重试策略与业务幂等"
description: "通过提交后超时实验理解重复执行与唯一键"
eyebrow: "LangGraph / 14"
---

# [codex] 重试策略与业务幂等

调用超时后重试一次，看起来能提高成功率。但如果数据库已经提交，只是响应丢了，第二次调用就可能重复写入。重试解决临时失败，幂等解决重复执行造成的业务后果，这两件事必须一起设计。

## 先限制哪些错误值得重试

实验 07 第一次 fetch 抛出 TimeoutError，第二次成功。策略明确指定异常类型与总尝试次数：

```python
policy = RetryPolicy(
    max_attempts=2,
    retry_on=TimeoutError,
    initial_interval=0,
    jitter=False,
)
builder.add_node("fetch", fetch, retry_policy=policy)
```

`max_attempts=2` 包含首次执行，不是失败后再执行两次。例子把等待设为 0 是为了快速观察；真实依赖应使用适当退避、超时和总预算。鉴权失败、参数错误通常需要修正原因，不能一律重试。

实验里的计数器只负责模拟先失败后成功，在进程重启后不会保留；它不是可靠的业务尝试记录。

## 完整示例：提交成功后模拟超时

```python
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
```

输出里有两次写入尝试，但数据库只有一条记录。第一次 INSERT 和 commit 已成功，随后抛出超时；第二次使用相同业务键 job-1，唯一约束和 `ON CONFLICT DO NOTHING` 让插入变成无操作。

## 真正起作用的是稳定的业务键

如果每次重试都生成新的随机 ID，唯一约束根本检测不到重复业务。键应在进入可重试步骤前确定，并且在重试、重入和恢复时保持稳定。

示例只有一个 id 字段，适合观察“只插入一次”。真实订单或发布请求还应校验同一个键是否对应同一份参数；同键不同载荷不能悄悄吞掉。必要时保存处理状态和结果，重复请求返回已有结果。

checkpoint 记录的是图的执行状态，外部系统提交有自己的事务边界。如果外部提交后、图保存完成前进程崩溃，恢复可能再调用外部系统；需要外部 API 的幂等键、事务设计或补偿机制来处理，不能只靠 LangGraph 保证恰好一次。

## 演示范围与工程选择

此例使用内存 SQLite，进程退出后记录消失。`check_same_thread=False` 是为了允许图执行器线程访问连接，不意味着这个连接可以任意并发写入；本图没有并行数据库节点。

将同样的代码放到扣款或发消息节点之前，仍要审查实际接收方是否支持去重。对不支持幂等的接口，应单独设计状态核对或人工处理流程。这是业务一致性选择，不是换一个 RetryPolicy 参数就能解决。

## 动手验证

先运行 07 和 21。将实验 07 的 max_attempts 改成 1，确认首次超时直接失败。再在实验 21 中去掉 `ON CONFLICT`，保留主键，第二次插入应出现唯一键冲突；这说明冲突是业务重复的证据，不能把它当作新的临时网络故障无限重试。

## 配套练习

运行命令均以 `examples/langgraph-mini-lab` 为当前目录；可点击文件查看完整源码。

| 实验 | 可运行文件 | 观察重点 |
|---|---|---|
| 07 | [节点自动重试](../../examples/langgraph-mini-lab/02_nodes/07_retry.py) | RetryPolicy 只重试指定异常；max_attempts 包含首次执行 |
| 21 | [重试时避免重复写入](../../examples/langgraph-mini-lab/04_nodes/21_idempotency.py) | 同一业务 id + 数据库唯一约束，让重复尝试只产生一条记录 |

## 小结

- 为可恢复的临时错误设置有限重试，次数包含首次执行。
- 稳定业务键和存储约束共同防止重复结果。
- 图恢复、外部事务和业务成功要分别核对。

机制参考：[Use the graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api)、[Durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)。

下一篇建议继续看：

- [[codex] 子图封装与结构化校验](../15-codex-subgraphs-validation/index.html)
