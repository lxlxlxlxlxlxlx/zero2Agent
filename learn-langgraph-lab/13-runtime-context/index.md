---
layout: default
title: "Runtime Context：把运行依赖与状态分开"
description: "通过 context 注入本轮配置"
eyebrow: "LangGraph 实验课 / 13"
---

# Runtime Context：把运行依赖与状态分开

同一张图在不同请求中使用不同问候前缀，难道要把每个配置都加入 State？本轮依赖和流程结果可以有不同的数据边界。

## 只看这个机制

**State 存过程数据，Runtime.context 提供本次调用依赖。** 使用 context_schema 声明结构，在 invoke 时注入，在节点中读取。

熟悉 Java 的读者可以类比请求级依赖与流程 DTO，但这里没有隐含的容器注入或事务语义。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_13.py`。导入、状态、节点和连线都在这个文件里。

```python
from dataclasses import dataclass
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime

@dataclass
class Context:
    prefix: str

class State(TypedDict):
    name: str
    text: str

def greet(state: State, runtime: Runtime[Context]) -> dict:
    return {"text": f"{runtime.context.prefix}, {state['name']}!"}

builder = StateGraph(State, context_schema=Context)
builder.add_node("greet", greet)
builder.add_edge(START, "greet")
builder.add_edge("greet", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"name": "小林"}, context=Context(prefix="Hello"))
    print(result["text"])
    assert result["text"] == "Hello, 小林!"
    assert "prefix" not in result
```

运行：

```bash
python lesson_13.py
```

## 读懂结果

```text
Hello, 小林!
```

同样的 name 与不同 prefix 可以生成不同问候语。返回 State 中没有 prefix，配置没有被节点写入状态。

### 代码抓住三处

1. context_schema 声明运行上下文，State 仍只保留业务过程字段。
2. 节点通过 `runtime.context` 读取前缀，不从全局变量读取。
3. invoke 的 context 参数供这轮运行使用；没有主动写入，就不会出现在返回 State 中。

## 动手改一处

把 prefix 改为 Welcome，预期输出 `Welcome, 小林!`。State 的字段定义不用修改。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

context 不会自动作为 State 保存到检查点。任务恢复时需要重新提供必要依赖；也不要为了方便把凭据复制进可能持久化的 State。

## 记住这一点

**让状态解释处理过程，让 Context 提供运行所需依赖。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [Checkpointer：同一会话延续，不同会话隔离](../14-checkpoint-threads/index.html)
