---
layout: default
title: "汇合屏障：等两个分支都完成"
description: "用不同字段隔离并行结果并明确汇合"
eyebrow: "LangGraph 实验课 / 07"
---

# 汇合屏障：等两个分支都完成

一段文本要同时统计词数和字符数，报告必须等两份结果都齐了才能生成。让两个分支“都指向报告”不如明确写出等待条件。

## 只看这个机制

**Fan-out 启动并行分支，Fan-in 定义汇合条件。** 两个分支分别写 words 和 chars，字段互不冲突；列表形式的 add_edge 明确等待两个指定节点都完成。

## 最小可运行代码

已完成[第 01 课的环境准备](../01-state-updates/index.html)即可运行；每个示例都是独立文件。

将下面代码保存为 `lesson_07.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    words: int
    chars: int
    report: str

def prepare(state: State) -> dict:
    return {"text": state["text"].strip()}

def count_words(state: State) -> dict:
    return {"words": len(state["text"].split())}

def count_chars(state: State) -> dict:
    return {"chars": len(state["text"])}

def make_report(state: State) -> dict:
    return {"report": f"单词 {state['words']}，字符 {state['chars']}"}

builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("count_words", count_words)
builder.add_node("count_chars", count_chars)
builder.add_node("make_report", make_report)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "count_words")
builder.add_edge("prepare", "count_chars")
builder.add_edge(["count_words", "count_chars"], "make_report")
builder.add_edge("make_report", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"text": " hi hi "})
    print(result["report"])
    assert (result["words"], result["chars"]) == (2, 5)
```

运行：

```bash
python lesson_07.py
```

## 读懂结果

```text
单词 2，字符 5
```

prepare 把输入清理成 `hi hi`，所以得到两个词、五个字符。make_report 读取两份结果后才输出。这里只并行两个确定要执行的分支。

### 代码抓住三处

1. prepare 只运行一次，再从同一节点分出两条边。
2. 两个统计节点分别拥有 words、chars，避免同一字段的并发覆盖。
3. `add_edge(["count_words", "count_chars"], "make_report")` 把两个完成条件合在一起。

## 动手改一处

把输入改为 `" hello world "`，清理后得到两个词、11 个字符。将原断言更新为 `(2, 11)`。

## 最容易踩的坑

同一超步的多个节点写同一个普通字段会触发并发更新冲突，不能依赖最后写入覆盖。两条互斥路径也不能使用等待双方完成的屏障。

## 记住这一点

**并行前确认字段所有权，汇总前明确等待谁。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/use-graph-api)。

下一篇建议继续看：

- [异步节点：把等待时间重叠起来](../08-async-nodes/index.html)
