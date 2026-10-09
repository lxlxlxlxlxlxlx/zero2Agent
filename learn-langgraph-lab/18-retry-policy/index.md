---
layout: default
title: "RetryPolicy：只重试可恢复的错误"
description: "限制异常类型与总尝试次数"
eyebrow: "LangGraph 实验课 / 18"
---

# RetryPolicy：只重试可恢复的错误

接口偶尔超时，重试可以恢复；参数写错，重复请求通常只会重复失败。先区分错误类型，再决定重试预算。

## 只看这个机制

**RetryPolicy 为节点定义哪些异常可以重试、总共尝试几次。** 本例第一次 fetch 抛 TimeoutError，第二次返回 7。计数器只模拟外部服务的行为。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_18.py`。导入、状态、节点和连线都在这个文件里。

```python
from itertools import count
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    value: int

attempts = count(1)

def fetch(state: State) -> dict:
    attempt = next(attempts)
    print(f"尝试 {attempt}")
    if attempt == 1:
        raise TimeoutError("模拟第一次调用超时")
    return {"value": 7}

policy = RetryPolicy(
    max_attempts=2, retry_on=TimeoutError, initial_interval=0, jitter=False
)
builder = StateGraph(State)
builder.add_node("fetch", fetch, retry_policy=policy)
builder.add_edge(START, "fetch")
builder.add_edge("fetch", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"value": 0})
    print(f"结果: {result['value']}")
    assert result["value"] == 7
```

运行：

```bash
python lesson_18.py
```

## 读懂结果

```text
尝试 1
尝试 2
结果: 7
```

打印尝试 1、尝试 2 后输出 7。max_attempts=2 包含首次执行，并不是失败后再额外尝试两次。

### 代码抓住三处

1. retry_on 只允许 TimeoutError 触发重试，其他异常继续向外抛出。
2. max_attempts 限制 fetch 总执行次数，成功返回后图才提交节点更新。
3. attempts 计数器模拟服务端先失败后成功，不负责保存业务状态。

## 动手改一处

把 max_attempts 改为 1，第一次超时应直接向外抛出；再改回 2，确认恢复成功。

## 最容易踩的坑

initial_interval=0 只为缩短教学等待。真实依赖需要退避、超时和总预算；进程内计数器也不能充当可靠的跨进程尝试记录。

## 记住这一点

**指定错误类型，限制总次数，再考虑重试。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [幂等：提交后超时，重试会不会重复写入](../19-idempotency/index.html)
