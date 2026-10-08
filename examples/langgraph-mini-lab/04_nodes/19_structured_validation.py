# 19｜结构化校验与一次修复
# 顶层业务节点：4（不计 START / END）
# 流程：START -> generate -> validate -> [repair -> validate 或 finish] -> END
# 重点：Pydantic model_validate_json、ValidationError、限制修复次数
# 预期：得分: 80 / repairs: 1
# 动手改：把初始 score 改成 90，观察 repairs 从 1 变为 0。
# 注意：JSON 来自固定字符串，不是真实模型；校验不等于保证事实正确。

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
