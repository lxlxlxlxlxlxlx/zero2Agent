---
layout: default
title: "[codex] 子图封装与结构化校验"
description: "设计子图数据边界并为输出修复设置终止条件"
eyebrow: "LangGraph / 15"
---

# [codex] 子图封装与结构化校验

图越来越大时，所有节点都读写一份巨大 State，会让修改一个计算步骤牵动整个流程。同时，即使模型返回了 JSON，也不代表下游可以直接使用。子图封装负责缩小内部耦合，结构化校验负责守住输出边界。

## 运行准备

在自己新建的练习目录中运行以下命令；本页所有实验代码都已完整展开，可以直接复制保存，不需要下载源码或依赖原始资料目录。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "langgraph==1.2.12" "langchain-core>=1.0,<2.0" "pydantic>=2.7.4,<3.0"
```

建议 Python 3.11 或以上；fish 用户用 `source .venv/bin/activate.fish` 激活。已在前一篇创建环境的读者可以继续使用同一环境。核心版本用于复现实验，其余依赖是范围约束；主练习不需要模型 API Key。

## 子图先定义输入与输出边界

实验 18 把平方、乘二放进一个已编译的子图。父图只关心 x 和 result，内部的 squared 不暴露给父图：

### 实验 18：子图封装与共享字段 {#experiment-18}

将下面的完整代码保存为 `18_subgraph.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

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
    report: str

def normalize(state: State) -> dict:
    return {"x": abs(state["x"])}

def format_report(state: State) -> dict:
    return {"report": f"结果: {state['result']}"}

def finish(state: State) -> dict:
    return {"report": state["report"] + "，完成"}

builder = StateGraph(State)
builder.add_node("normalize", normalize)
builder.add_node("worker", child)
builder.add_node("format_report", format_report)
builder.add_node("finish", finish)
builder.add_edge(START, "normalize")
builder.add_edge("normalize", "worker")
builder.add_edge("worker", "format_report")
builder.add_edge("format_report", "finish")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"x": -3})
    print(result["report"])
    assert result["result"] == 18
    assert "squared" not in result
```

运行：

```bash
python 18_subgraph.py
```

预期输出：

```text
结果: 18，完成
```

父图先把 -3 规范化为 3，子图算出 18，父图再格式化报告。顶层仍是四个业务节点，worker 内部另有两个节点，不能把节点定义数和实际执行次数混为一谈。

这种直接挂载依赖父子图共享字段。如果两边 schema 不同，需要包装节点显式转换输入和输出。子图复用不自动等于多 Agent；这里没有独立的模型角色、权限或调度系统。

## JSON 能解析，不代表内容满足约束

实验 19 故意生成 `{"score": 120}`。它是合法 JSON，但不满足分数 0–100 的约束。通过 Pydantic 捕获失败后，只允许修复一次：

### 实验 19：结构化校验与一次修复 {#experiment-19}

将下面的完整代码保存为 `19_structured_validation.py`。各实验分别保存、独立运行，不要把多个实验拼进同一个文件。

```python
from typing import TypedDict
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, START, END

class Score(BaseModel):
    score: int = Field(ge=0, le=100, strict=True)

class State(TypedDict):
    raw: str
    parsed: dict
    error: str
    repairs: int
    report: str

def generate(state: State) -> dict:
    return {"raw": '{"score": 120}'}  # 模拟模型输出，故意越界。

def validate(state: State) -> dict:
    try:
        parsed = Score.model_validate_json(state["raw"]).model_dump()
        return {"parsed": parsed, "error": ""}
    except ValidationError:
        return {"parsed": {}, "error": "score 必须是 0 到 100 的整数"}

def route(state: State) -> str:
    if state["error"] and state["repairs"] < 1:
        return "repair"
    return "finish"

def repair(state: State) -> dict:
    return {"raw": '{"score": 80}', "repairs": state["repairs"] + 1}

def finish(state: State) -> dict:
    text = state["error"] or f"得分: {state['parsed']['score']}"
    return {"report": text}

builder = StateGraph(State)
builder.add_node("generate", generate)
builder.add_node("validate", validate)
builder.add_node("repair", repair)
builder.add_node("finish", finish)
builder.add_edge(START, "generate")
builder.add_edge("generate", "validate")
builder.add_conditional_edges("validate", route, ["repair", "finish"])
builder.add_edge("repair", "validate")
builder.add_edge("finish", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"repairs": 0}, {"recursion_limit": 12})
    print(result["report"])
    print("repairs:", result["repairs"])
    assert result["parsed"] == {"score": 80} and result["repairs"] == 1
```

运行：

```bash
python 19_structured_validation.py
```

预期输出：

```text
得分: 80
repairs: 1
```

这里 `strict=True` 避免把字符串分数悄悄转换为整数，`ge/le` 约束范围。错误返回时清空 parsed，成功时清空 error，防止前一轮的状态残留影响本轮判断。

generate 和 repair 都返回固定字符串，没有调用模型，也没有演示服务端原生结构化输出。真实接入时可以替换生成与修复节点，保留校验和退出逻辑，另行验证模型输出质量。

## 修复失败也要能正常结束

路由只在有错误且 repairs 小于 1 时进入 repair。若修复仍产生 120，下一轮 validate 继续报错，随后 finish 返回错误信息。流程有终点，不意味着内容被修复成功。

这是有限修复循环，和网络超时重试有不同含义：前者需要基于校验错误生成新候选，后者往往重发同一请求。把所有 ValidationError 都交给 RetryPolicy，可能只会重复得到同一个错误结果。

校验器能判断字段和范围，无法证明评分有事实依据。业务质量还需要参考答案、领域规则或人工评价；不能把 schema 通过率直接写成 Agent 正确率。

## 动手验证与验收范围

实验 18 将乘二改为乘三，预期得到 27，父图连线不用改。实验 19 将初始分数改为 90，预期 repairs 为 0；再将修复结果也改成 120，确认有限次后输出错误。

恢复原始参数后，分别执行本页两个脚本，确认输出和断言均通过。本系列的 21 个主练习都已通过整图执行验证，包括实验 20 的四进程 SQLite 恢复；选学 22 只检查代码语法，没有连接真实模型，不计入主练习通过数。

读者按每个实验下方的命令逐项运行即可，无需另行取得自测脚本、manifest 或原始练习包。修改实验参数后同步调整断言，并明确区分语法通过、图运行通过和业务结果正确。

## 本页实验回顾

| 实验 | 已展开的内容 |
|---|---|
| 18 | 子图封装与共享字段 |
| 19 | 结构化校验与一次修复 |

## 小结

- 子图通过明确的数据边界减小耦合，内部字段不必全部暴露。
- 结构校验与业务质量是两层判断，修复也必须有失败出口。
- 静态检查、整图执行和真实模型验证需要分别记录。

机制参考：[Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)、[Pydantic Fields](https://docs.pydantic.dev/latest/concepts/fields/)。

本系列到这里结束。下一篇建议继续看：

- [工具系统：MCP 与并行执行](../../learn-openclaw/04-tools/index.html)
