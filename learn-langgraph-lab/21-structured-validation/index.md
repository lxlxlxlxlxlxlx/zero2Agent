---
layout: default
title: "结构化校验：合法 JSON 也可能不合格"
description: "对输出加约束并限制修复次数"
eyebrow: "LangGraph 实验课 / 21"
---

# 结构化校验：合法 JSON 也可能不合格

模型返回了 JSON，下游却拿到 120 分。能解析只说明语法有效，不能证明字段符合业务范围，更不能证明内容有事实依据。

## 只看这个机制

**Pydantic 校验字段约束，图负责失败后的有限修复。** strict=True 限制类型，ge/le 限制范围；失败时清空 parsed，成功时清空 error，避免旧状态残留。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_21.py`。导入、状态、节点和连线都在这个文件里。

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
python lesson_21.py
```

## 读懂结果

```text
得分: 80
repairs: 1
```

第一份分数越界，进入 repair；修复为 80 后通过，repairs=1。generate 与 repair 都是固定字符串，演示没有接真实模型。

### 代码抓住三处

1. `model_validate_json` 同时解析 JSON 并校验字段，失败会抛 ValidationError。
2. route 根据 error 和 repairs 判断是否还有修复额度。
3. 每次修复都回到 validate 重新校验；耗尽额度后由 finish 输出错误。

## 动手改一处

先把初始分数改为 90，修复次数应为 0；再把初始值和修复值都改为 120，确认只修复一次后输出错误，流程仍能结束。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

次数耗尽也会进入 finish，需要检查 error 才能判断成功。结构校验无法证明评分真实；语义修复需要新候选，不能直接等同于重发同一请求的网络重试。

## 记住这一点

**校验输出契约，并给修复失败留出明确出口。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-graph-api)、[Pydantic 字段约束](https://docs.pydantic.dev/latest/concepts/fields/)。

下一篇建议继续看：

- [接入真实模型：只替换决策节点](../22-real-model/index.html)
