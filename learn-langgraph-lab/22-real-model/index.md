---
layout: default
title: "接入真实模型：只替换决策节点"
description: "将确定性工具闭环换成模型驱动"
eyebrow: "LangGraph 实验课 / 22"
---

# 接入真实模型：只替换决策节点

确定性工具闭环已经跑通，接入真实模型后却没有执行工具。此时需要区分模型选择、服务兼容性与图连线，避免把问题全部归给 Prompt。

## 只看这个机制

**bind_tools 提供工具描述，模型返回调用意图，原来的 ToolNode 执行链继续工作。** 与工具闭环课对照，工具函数和路由基本不变，模型节点换成真正的 invoke。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

本课额外安装：

```bash
python -m pip install "langchain-openai>=1.0,<2.0"
```

将下面代码保存为 `lesson_22.py`。导入、状态、节点和连线都在这个文件里。

```python
import os
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

@tool
def add(a: int, b: int) -> int:
    """返回两个整数的和。"""
    return a + b

def call_model(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode([add]))
builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", tools_condition, {"tools": "tools", END: END})
builder.add_edge("tools", "call_model")
graph = builder.compile()

if __name__ == "__main__":
    model_name = os.environ.get("LLM_MODEL")
    if not model_name:
        raise SystemExit("请先设置 LLM_MODEL，使用服务实际提供的模型名。")
    llm = ChatOpenAI(
        model=model_name,
        base_url=os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8080/v1"),
        api_key=os.environ.get("LLM_API_KEY", "local-not-used"),
        timeout=30,
        max_retries=0,
    ).bind_tools([add])
    result = graph.invoke(
        {"messages": [HumanMessage(content="请调用 add 工具计算 3 + 4，然后回答结果。")]},
        {"recursion_limit": 10},
    )
    print(result["messages"][-1].content)
    for message in result["messages"]:
        print(message.type, message.content)
        if getattr(message, "tool_calls", None):
            print("工具请求:", message.tool_calls)
        if getattr(message, "tool_call_id", None):
            print("对应调用:", message.tool_call_id)
```

运行：

```bash
export LLM_MODEL="服务实际提供的模型名"
export LLM_BASE_URL="http://127.0.0.1:8080/v1"
python lesson_22.py
```

## 读懂结果

本课没有固定输出，未纳入确定性运行验收。需要自行准备一个已启动、支持工具调用的模型服务。

输出不会固定。检查消息轨迹是否出现 tool，并确认最终答案使用了相应结果；只得到正确数字，不能证明工具被调用。

fish 使用 `set -gx LLM_MODEL "服务实际提供的模型名"` 等价设置变量。远程服务需要的 `LLM_API_KEY` 也从环境注入；默认本机地址的占位 Key 只适用于无需认证的本地服务。

### 代码抓住三处

1. `bind_tools([add])` 将工具说明交给模型，并不执行 add。
2. 模型节点把当前 messages 发给服务，再将返回消息提交给图。
3. 后续工具执行、消息回填和条件路由，与第 11 课使用同一套机制。

## 动手改一处

将问题改成“请调用 add 计算 10 加 20”。观察参数是否改变、tool_call_id 是否匹配、最终结果是否为 30；保留实际轨迹，不强行把模型输出断言成固定句子。

## 最容易踩的坑

服务必须支持工具 schema 和工具调用返回格式。示例不会启动或下载模型；本课未连接真实服务验证。远程认证通过环境变量提供，不将 Key 写入代码。

## 记住这一点

**替换模型节点后，重新验证调用轨迹与实际结果。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/workflows-agents)。

下一篇建议继续看：

- [LangGraph 实验课：验收清单](../index.html#验收清单)
