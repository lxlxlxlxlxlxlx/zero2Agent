---
layout: default
title: "[codex] 最小实验：State、Reducer 与状态流"
description: "用四个双节点实验看清状态更新、消息替换和流式输出"
eyebrow: "LangGraph / 08"
---

# [codex] 最小实验：State、Reducer 与状态流

如果每次节点运行后都把完整状态打印出来，最终答案也许正确，但你仍不知道列表为什么重复、修订消息为什么变成两条。先用不调用模型的小图隔离这些问题，后面的工具循环和恢复才容易排查。

本系列把用户提供的 `langgraph_mini_lab` 改编成 8 篇工程教程，覆盖 21 个主练习和 1 个选学例子。文章按问题组织，实验保留原来的 01–22 编号；两套编号不要混淆。所谓双节点、三节点、四节点，只数顶层 `add_node()`，不包括 `START`、`END` 和路由函数。

## 先跑通，再解释

在仓库根目录执行以下命令。建议 Python 3.11 或以上，主练习不需要模型 API Key。

```bash
cd examples/langgraph-mini-lab
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python 02_nodes/01_state_sequence.py
```

fish 用户将激活命令换为 `source .venv/bin/activate.fish`。实验固定 `langgraph==1.2.12`；这是复现基线，不代表最新版本，其他依赖仍是范围约束。全部主练习与验证说明见[配套实验入口](../../examples/langgraph-mini-lab/index.html)。

每个实验都按同一个节奏学习：**预测状态 → 运行原例 → 只改一个变量 → 解释差异**。修改输入后也要更新相应断言，旧断言失败不等于框架坏了。

## 局部更新：字段什么时候出现

实验 01 的输入只有 `text`，`count_words` 执行后才出现 `word_count`。节点返回 `{"word_count": 2}` 不会删除已有的 `text`。`TypedDict` 为静态检查和图的 schema 提供信息，不会替你初始化缺失字段，也不做 Python 字典的运行时类型校验。

把 `count_words` 移到 `clean` 前面，思考它读取的值有什么变化；把输入里的 `text` 删掉，则会因为读取不存在的键而失败。状态设计首先是先写后读的数据依赖设计。

## Reducer：覆盖和追加是两种契约

下面是实验 02 的完整代码，可以保存后独立运行：

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    latest: str
    history: Annotated[list[str], operator.add]

def first(state: State) -> dict:
    return {"latest": "A", "history": ["A"]}

def second(state: State) -> dict:
    return {"latest": "B", "history": ["B"]}

builder = StateGraph(State)
builder.add_node("first", first)
builder.add_node("second", second)
builder.add_edge(START, "first")
builder.add_edge("first", "second")
builder.add_edge("second", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"latest": "", "history": []})
    print("latest:", result["latest"])
    print("history:", result["history"])
    assert result["latest"] == "B"
    assert result["history"] == ["A", "B"]
```

这张图依次产生 A、B。普通字段 `latest` 最终是 B，追加字段 `history` 是 A、B 两项。关键在 `second` 只返回新增量 `["B"]`。

| second 返回的 history | 合并后的结果 | 原因 |
|---|---|---|
| `["B"]` | `["A", "B"]` | 追加新增量 |
| `state["history"] + ["B"]` | `["A", "A", "B"]` | 旧值被重复合并 |
| `[]` | `["A"]` | 追加空列表不会清空历史 |

“只返回变化字段”是减少歧义的工程习惯；返回完整字典并非一律语法非法，但对追加字段容易制造重复数据。

## 消息不能只按普通列表处理

实验 03 先写 `AIMessage(id="answer-1", content="初稿")`，再返回同 ID 的修订稿。`MessagesState` 的 `add_messages` 会更新原消息。将第二个 ID 改为 `answer-2`，两条 AI 消息就会同时保留。

普通 `operator.add` 不认识消息 ID。选择 reducer 前要先决定业务语义：追加事件、替换同一对象，还是合并数值。这里的 AIMessage 是手工构造的，出现 AI 消息不代表调用过模型。

## 流式：观察更新还是观察快照

实验 04 从 `n=1` 开始，先加一，再乘二：

```text
updates: [{'increment': {'n': 2}}, {'double': {'n': 4}}]
values: [{'n': 1}, {'n': 2}, {'n': 4}]
```

`updates` 适合解释哪个节点写了什么，`values` 适合观察每个超步后的完整状态；初始状态也会出现在这个例子的 values 流里。两次调用 `stream()` 会执行两轮图，带副作用的图不能为了换个观察方式随意重跑。

本系列沿用 stream-mode API 的默认 v1 返回格式。显式传 `version="v2"` 后要按 `type/ns/data` 读取，不能继续照搬这里的原始字典解析。节点状态流也不等于 Token 流；Token 流需要模型调用及相应的消息流模式。参见 [Streaming 官方文档](https://docs.langchain.com/oss/python/langgraph/streaming)。

## 动手验证

运行实验 01–04。把实验 04 的初始值改成 3，先写下 updates 的两个值和 values 的三个值，再验证。答案应分别为 4、8 与 3、4、8。

## 配套练习

运行命令均以 `examples/langgraph-mini-lab` 为当前目录；可点击文件查看完整源码。

| 实验 | 可运行文件 | 观察重点 |
|---|---|---|
| 01 | [状态与局部更新](../../examples/langgraph-mini-lab/02_nodes/01_state_sequence.py) | TypedDict、读取 State、只返回本节点修改的字段 |
| 02 | [覆盖与追加的区别](../../examples/langgraph-mini-lab/02_nodes/02_reducer.py) | Annotated[list[str], operator.add] 为一个字段设置 reducer |
| 03 | [消息按 ID 更新](../../examples/langgraph-mini-lab/02_nodes/03_message_ids.py) | MessagesState 内置 add_messages；同 ID 更新，新 ID 追加 |
| 04 | [节点更新与完整状态流](../../examples/langgraph-mini-lab/02_nodes/04_stream.py) | `stream_mode="updates"` 与 `stream_mode="values"` 的区别 |

## 小结

- 先确认字段的生产者，再让后续节点读取它。
- reducer 定义更新的含义；返回全量和返回增量不能混用。
- 消息 ID、执行次数和流式格式都要明确，才能解释观察结果。

机制参考：[Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [[codex] State、Context 与跨会话记忆](../09-codex-context-memory/index.html)
