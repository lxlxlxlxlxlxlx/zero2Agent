---
layout: default
title: "工具闭环：请求、执行、结果回填"
description: "用固定模型决策跑通真实工具调用"
eyebrow: "LangGraph 实验课 / 11"
---

# 工具闭环：请求、执行、结果回填

模型生成了“调用 add”的请求，函数并不会自己运行。要验证工具闭环，需要沿消息轨迹确认请求被执行、结果被关联、回答又使用了结果。

## 只看这个机制

**模型节点产生意图，ToolNode 执行函数，ToolMessage 把结果送回模型节点。** 本课用固定规则代替模型决策，让计算结果完全可复现；工具本身仍由 LangGraph 真正调用。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_11.py`。导入、状态、节点和连线都在这个文件里。

```python
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

@tool
def add(a: int, b: int) -> int:
    """返回两个整数的和。"""
    return a + b

def model(state: MessagesState) -> dict:
    last = state["messages"][-1]
    if isinstance(last, ToolMessage):
        return {"messages": [AIMessage(content=f"答案: {last.content}")]}
    call = {"name": "add", "args": {"a": 3, "b": 4}, "id": "call-1", "type": "tool_call"}
    return {"messages": [AIMessage(content="", tool_calls=[call])]}

builder = StateGraph(MessagesState)
builder.add_node("model", model)
builder.add_node("tools", ToolNode([add]))
builder.add_edge(START, "model")
builder.add_conditional_edges("model", tools_condition, {"tools": "tools", END: END})
builder.add_edge("tools", "model")
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"messages": [HumanMessage(content="计算 3 + 4")]},
                          {"recursion_limit": 10})
    messages = result["messages"]
    print(result["messages"][-1].content)
    print([message.type for message in messages])
    assert messages[-1].content == "答案: 7"
    assert messages[2].tool_call_id == messages[1].tool_calls[0]["id"]
    assert [message.type for message in messages] == ["human", "ai", "tool", "ai"]
```

运行：

```bash
python lesson_11.py
```

## 读懂结果

```text
答案: 7
['human', 'ai', 'tool', 'ai']
```

四条消息依次为 human、ai、tool、ai。ToolMessage 的 tool_call_id 对应前一条 AI 消息里的调用 ID，答案为 7。改提问文本不会自动改变写死的工具参数。

### 代码抓住三处

1. 第一次模拟模型调用构造带名称、参数和 ID 的工具请求。
2. `tools_condition` 根据最后一条消息是否包含工具请求来选择分支。
3. ToolNode 执行 add 后返回 ToolMessage；回到模型节点再生成最终答案。

## 动手改一处

把工具请求中的 a、b 改为 10、20，预期答案为 30；更新答案断言，保留 ID 对应关系的检查。

## 最容易踩的坑

AIMessage 自身的 id 用于消息更新，tool_calls 中的 id 用于调用配对。真实服务还需在工具执行前做参数和权限校验，模型请求本身不等于业务授权。

## 记住这一点

**闭环的证据是消息与工具执行链条，不能只看最终一句答案。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/workflows-agents)。

下一篇建议继续看：

- [模型上下文：历史保存多少，本轮发送多少](../12-model-context/index.html)
