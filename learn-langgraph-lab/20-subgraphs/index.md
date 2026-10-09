---
layout: default
title: "子图：隐藏内部步骤，保留数据接口"
description: "通过共享字段组合父图与子图"
eyebrow: "LangGraph 实验课 / 20"
---

# 子图：隐藏内部步骤，保留数据接口

一组计算步骤需要在多个流程中复用，如果把内部中间值全部暴露给父图，每次修改都会影响调用方。子图提供一个更小的接口。

## 只看这个机制

**已编译的子图可以作为父图节点，共享字段用于衔接数据。** 父图关心 x 与 result；子图内部还有 squared。父图负责规范化输入，子图负责计算。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_20.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class ChildState(TypedDict):
    x: int
    squared: int
    result: int

def square(state: ChildState) -> dict:
    return {"squared": state["x"] ** 2}

def double(state: ChildState) -> dict:
    return {"result": state["squared"] * 2}

child_builder = StateGraph(ChildState)
child_builder.add_node("square", square)
child_builder.add_node("double", double)
child_builder.add_edge(START, "square")
child_builder.add_edge("square", "double")
child_builder.add_edge("double", END)
child = child_builder.compile()

class State(TypedDict):
    x: int
    result: int

def normalize(state: State) -> dict:
    return {"x": abs(state["x"])}

builder = StateGraph(State)
builder.add_node("normalize", normalize)
builder.add_node("worker", child)
builder.add_edge(START, "normalize")
builder.add_edge("normalize", "worker")
builder.add_edge("worker", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"x": -3})
    print(f"结果: {result['result']}")
    assert result["result"] == 18
    assert "squared" not in result
```

运行：

```bash
python lesson_20.py
```

## 读懂结果

```text
结果: 18
```

-3 先变成 3，再平方、乘二，得到 18。父图结果中没有 squared，说明调用方无需依赖这个内部字段。

### 代码抓住三处

1. 子图先独立 compile，再作为父图中的 worker 节点加入。
2. x 与 result 是共享字段，squared 只在子图的 schema 中。
3. 父图只关心输入规范化与最终结果，不连接子图的内部节点。

## 动手改一处

把子图中的乘二改成乘三，结果应为 27。父图连线不需要修改；更新结果断言即可。

## 最容易踩的坑

直接挂载要求有可衔接的共享字段。schema 不同应写包装节点转换输入输出。子图封装也不等于独立 Agent，本例没有模型角色或权限隔离。

## 记住这一点

**对外稳定数据接口，对内允许计算步骤变化。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)。

下一篇建议继续看：

- [结构化校验：合法 JSON 也可能不合格](../21-structured-validation/index.html)
