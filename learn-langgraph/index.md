---
layout: default
title: learn-langgraph
description: 用七篇基础教程理解状态图、条件分支、并行执行与模型接入
eyebrow: Module 02
---

# learn-langgraph

链式调用能跑通 Demo，但一旦加入条件分支、循环和错误恢复，代码就会变成意大利面。

LangGraph 用**图结构**来描述 Agent 的执行逻辑：节点是操作，边是转移，状态是贯穿全程的上下文。这不只是换了一种写法，而是换了一种思维方式——从“怎么写代码”变成“怎么设计状态机”。

## 这个模块覆盖什么

<div style="overflow-x: auto;" markdown="1">

| # | 文章 | 你会学到什么 |
|---|------|------------|
| 01 | [LangGraph 是什么，为什么不用链式调用](01-what-is-langgraph/index.html) | 链式调用的局限，图结构的优势，核心抽象 |
| 02 | [State、Node、Graph 三件套](02-state-node-graph/index.html) | TypedDict 状态设计，节点函数签名，编译与运行 |
| 03 | [顺序图：第一个可运行的 Workflow](03-sequential-graph/index.html) | add\_edge 模式，多节点顺序流，实战 BMI 计算器 |
| 04 | [条件分支：add\_conditional\_edges](04-conditional-edges/index.html) | 路由函数，情感分析路由，Pydantic 结构化输出 |
| 05 | [并行执行：Fan-out / Fan-in](05-parallel-workflows/index.html) | 多节点同时启动，汇聚节点，cricket 统计实战 |
| 06 | [Prompt Chaining：分步生成](06-prompt-chaining/index.html) | 拆解生成任务，节点间传递中间结果，HuggingFace 集成 |
| 07 | [接入 LLM：OpenAI 与 HuggingFace](07-llm-integration/index.html) | ChatOpenAI，HuggingFaceEndpoint，在节点里调用模型 |

</div>

## 建议阅读顺序

按 01–07 顺序阅读，先理解图的三个核心概念，再练习顺序、分支、并行与模型接入。

想用小例子逐项验证机制，继续学习独立的 [LangGraph 实验课](../learn-langgraph-lab/index.html)。22 节课程按一个知识点一份完整代码组织。

## 前置知识

- 读过 [Agent Basic](../learn-agent-basic/index.html) 或者知道什么是 Agent、Tool Calling
- 会写基本的 Python，知道 `TypedDict` 是什么
- 不需要 LangGraph 经验

## 从哪里开始

如果完全没接触过 LangGraph，从 [第 01 篇](01-what-is-langgraph/index.html) 开始读。

如果已经知道 LangGraph 是状态图，想直接上手，从 [第 02 篇](02-state-node-graph/index.html) 开始。
