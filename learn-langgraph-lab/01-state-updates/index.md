---
layout: default
title: "State：节点只交回变化的字段"
description: "用两个节点看清状态读取与局部更新"
eyebrow: "LangGraph 实验课 / 01"
---

# State：节点只交回变化的字段

清理文本后还要统计词数，两个函数之间到底传什么？先把数据流看清，再接模型，出了错才能知道是哪一步写错了状态。

## 只看这个机制

**State 是节点之间传递的过程数据，节点返回值是一次更新。** 本例只保留 text 和 word_count。clean 写 text，count_words 读取清理后的 text，再写 word_count。

TypedDict 描述键和值的类型，方便静态检查和图读取 schema；它不会替你创建字典里的字段。

## 最小可运行代码

在已准备好的 Python 3.11+ 环境中运行；首次学习可在空目录执行：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install "langgraph==1.2.12" "langchain-core==1.6.7" "pydantic==2.13.5"
```

fish 的激活命令为 `source .venv/bin/activate.fish`。其他课程沿用这个环境即可。

将下面代码保存为 `lesson_01.py`。导入、状态、节点和连线都在这个文件里。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str
    word_count: int

def clean(state: State) -> dict:
    return {"text": state["text"].strip()}

def count_words(state: State) -> dict:
    return {"word_count": len(state["text"].split())}

builder = StateGraph(State)
builder.add_node("clean", clean)
builder.add_node("count_words", count_words)
builder.add_edge(START, "clean")
builder.add_edge("clean", "count_words")
builder.add_edge("count_words", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"text": "  hello graph  "})
    print(result)
    assert result == {"text": "hello graph", "word_count": 2}
```

运行：

```bash
python lesson_01.py
```

## 读懂结果

```text
{'text': 'hello graph', 'word_count': 2}
```

输入只有 text，输出多了 word_count。第二个节点没有返回 text，它仍然保留；这就是局部更新。split() 按空白分词，不能用这个结果衡量中文词数。

### 代码抓住三处

1. `StateGraph(State)` 声明图中有哪些字段；输入可以先只提供第一个节点需要的数据。
2. `return {"text": ...}` 更新一个字段，不会清空其他字段。
3. `START → clean → count_words → END` 保证先清理，再读取清理后的文本。

## 动手改一处

把输入换成 `"  hello graph world  "`，先预测结果，再运行。word_count 应为 3，text 两端的空白应消失。

如果修改了预期结果，也要同步修改示例末尾对应的 `assert`。

## 最容易踩的坑

节点读取一个尚未写入的字段仍会抛 KeyError。画图之前先列出每个字段由谁写、被谁读；不要把 TypedDict 当成默认值生成器。

## 记住这一点

**先找数据的生产者，再连依赖它的节点。**

API 依据：[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。

下一篇建议继续看：

- [Reducer：列表为什么会重复](../02-reducers/index.html)
