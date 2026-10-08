# 01｜状态与局部更新
# 顶层业务节点：2（不计 START / END）
# 流程：START -> clean -> count_words -> END
# 重点：TypedDict、读取 State、只返回本节点修改的字段
# 预期：{'text': 'hello graph', 'word_count': 2}
# 动手改：把输入改成 "  hello graph world  "，预测 word_count。
# 注意：split() 按空白分词，不是中文分词；TypedDict 不做运行时校验。

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
