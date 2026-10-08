---
layout: default
title: "[codex] 子图封装与结构化校验"
description: "设计子图数据边界并为输出修复设置终止条件"
eyebrow: "LangGraph / 15"
---

# [codex] 子图封装与结构化校验

图越来越大时，所有节点都读写一份巨大 State，会让修改一个计算步骤牵动整个流程。同时，即使模型返回了 JSON，也不代表下游可以直接使用。子图封装负责缩小内部耦合，结构化校验负责守住输出边界。

## 子图先定义输入与输出边界

实验 18 把平方、乘二放进一个已编译的子图。父图只关心 x 和 result，内部的 squared 不暴露给父图：

```python
class ChildState(TypedDict):
    x: int
    squared: int
    result: int

class State(TypedDict):
    x: int
    result: int
    report: str

# child 是由 ChildState 构建、编译完成的图。
builder.add_node("worker", child)
```

上面是接口片段，完整代码见实验 18。父图先把 -3 规范化为 3，子图算出 18，父图再格式化报告。顶层仍是四个业务节点，worker 内部另有两个节点，不能把节点定义数和实际执行次数混为一谈。

这种直接挂载依赖父子图共享字段。如果两边 schema 不同，需要包装节点显式转换输入和输出。子图复用不自动等于多 Agent；这里没有独立的模型角色、权限或调度系统。

## JSON 能解析，不代表内容满足约束

实验 19 故意生成 `{"score": 120}`。它是合法 JSON，但不满足分数 0–100 的约束。通过 Pydantic 捕获失败后，只允许修复一次：

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

这里 `strict=True` 避免把字符串分数悄悄转换为整数，`ge/le` 约束范围。错误返回时清空 parsed，成功时清空 error，防止前一轮的状态残留影响本轮判断。

generate 和 repair 都返回固定字符串，没有调用模型，也没有演示服务端原生结构化输出。真实接入时可以替换生成与修复节点，保留校验和退出逻辑，另行验证模型输出质量。

## 修复失败也要能正常结束

路由只在有错误且 repairs 小于 1 时进入 repair。若修复仍产生 120，下一轮 validate 继续报错，随后 finish 返回错误信息。流程有终点，不意味着内容被修复成功。

这是有限修复循环，和网络超时重试有不同含义：前者需要基于校验错误生成新候选，后者往往重发同一请求。把所有 ValidationError 都交给 RetryPolicy，可能只会重复得到同一个错误结果。

校验器能判断字段和范围，无法证明评分有事实依据。业务质量还需要参考答案、领域规则或人工评价；不能把 schema 通过率直接写成 Agent 正确率。

## 动手验证与整包验收

实验 18 将乘二改为乘三，预期得到 27，父图连线不用改。实验 19 将初始分数改为 90，预期 repairs 为 0；再将修复结果也改成 120，确认有限次后输出错误。

恢复原例和断言后，在实验目录运行：

```bash
python check_syntax.py
python run_all.py
python -m pip install -r requirements-sqlite.txt
python run_all.py --sqlite
```

默认执行 20 个主练习，第 20 课显示 SKIP；加 `--sqlite` 才覆盖全部 21 个。SQLite 恢复会用临时数据库运行 start、status、resume、status 四个独立进程。真实模型选学 22 始终不计入这组确定性检查。

## 配套练习

运行命令均以 `examples/langgraph-mini-lab` 为当前目录；可点击文件查看完整源码。

| 实验 | 可运行文件 | 观察重点 |
|---|---|---|
| 18 | [子图封装与共享字段](../../examples/langgraph-mini-lab/04_nodes/18_subgraph.py) | 编译后的子图可作为父图节点；父子图通过共享字段衔接 |
| 19 | [结构化校验与一次修复](../../examples/langgraph-mini-lab/04_nodes/19_structured_validation.py) | Pydantic model_validate_json、ValidationError、限制修复次数 |

## 小结

- 子图通过明确的数据边界减小耦合，内部字段不必全部暴露。
- 结构校验与业务质量是两层判断，修复也必须有失败出口。
- 静态检查、整图执行和真实模型验证需要分别记录。

机制参考：[Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)、[Pydantic Fields](https://docs.pydantic.dev/latest/concepts/fields/)。

本系列到这里结束。下一篇建议继续看：

- [工具系统：MCP 与并行执行](../../learn-openclaw/04-tools/index.html)
