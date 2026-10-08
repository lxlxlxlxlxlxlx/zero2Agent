# 15｜四节点菱形汇总
# 顶层业务节点：4（不计 START / END）
# 流程：START -> prepare -> [count_words 与 count_chars] -> make_report -> END
# 重点：先准备数据再并行；并行写不同字段不需要追加 reducer
# 预期：单词 2，字符 5
# 动手改：把输入换为 "hello world"，预测单词数和字符数。
# 注意：汇总使用 add_edge([两个分支], make_report)，明确等待两个分支。

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
