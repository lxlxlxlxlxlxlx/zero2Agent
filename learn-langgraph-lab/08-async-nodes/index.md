---
layout: default
title: "异步节点：把等待时间重叠起来"
description: "用 ainvoke 与 astream 驱动异步分支"
eyebrow: "LangGraph 实验课 / 08"
---

# 异步节点：把等待时间重叠起来

两个接口请求彼此独立，却被顺序等待，响应时间就会累加。异步节点让等待重叠，但结果如何合并仍要由图明确表达。

## 只看这个机制

**async/await 表达 I/O 等待，图的边表达依赖。** left 与 right 同时启动，都向 values 返回一个数；追加 reducer 收集结果，collect 等待两边后求和。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_08.py`。导入、状态、节点和连线都在这个文件里。

```python
import asyncio
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    values: Annotated[list[int], operator.add]
    total: int

async def left(state: State) -> dict:
    await asyncio.sleep(0.02)
    return {"values": [5]}

async def right(state: State) -> dict:
    await asyncio.sleep(0.01)
    return {"values": [8]}

def collect(state: State) -> dict:
    return {"total": sum(state["values"])}

builder = StateGraph(State)
builder.add_node("left", left)
builder.add_node("right", right)
builder.add_node("collect", collect)
builder.add_edge(START, "left")
builder.add_edge(START, "right")
builder.add_edge(["left", "right"], "collect")
builder.add_edge("collect", END)
graph = builder.compile()

async def main() -> None:
    result = await graph.ainvoke({"values": []})
    print("ainvoke:", result["total"])
    snapshots = []
    async for snapshot in graph.astream({"values": []}, stream_mode="values"):
        snapshots.append(snapshot)
    print("astream:", snapshots[-1]["total"])
    assert sorted(result["values"]) == [5, 8]
    assert result["total"] == snapshots[-1]["total"] == 13

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python lesson_08.py
```

## 读懂结果

```text
ainvoke: 13
astream: 13
```

两种执行入口都得到 13。ainvoke 返回最终状态，astream 在执行过程中提供快照。例子调用两次，因此图执行了两轮。

### 代码抓住三处

1. `async def` 中的 await 让出等待时间，不能用同步阻塞调用替代。
2. values 使用追加 reducer，两边各提交一个数，合并后再求和。
3. `ainvoke` 用 await，`astream` 用 async for；二者分别启动一轮执行。

## 动手改一处

把 right 返回的 8 改成 10，总和应为 15。不要根据哪边 sleep 更短，就给结果列表的先后顺序写断言。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

异步不会自动加速 CPU 密集计算。真实请求还需要超时、取消和并发限制；模拟 sleep 只能验证调度路径，不能证明下游服务承受得住并发。

## 记住这一点

**异步减少等待，reducer 合并数据，屏障保证结果齐全。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [Send：按输入数量分发任务](../09-dynamic-send/index.html)
