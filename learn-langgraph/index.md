---
layout: default
title: learn-langgraph
description: 从图基础到 codex 最小实验，练习工具闭环、记忆、恢复与幂等
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
| 08 | [[codex] 最小实验：State、Reducer 与状态流](08-codex-state-reducers-stream/index.html) | 用四个双节点实验看清状态更新、消息替换和流式输出 |
| 09 | [[codex] State、Context 与跨会话记忆](09-codex-context-memory/index.html) | 分清会话状态、运行依赖和跨线程记忆的生命周期 |
| 10 | [[codex] 条件路由、循环与 Command](10-codex-routing-loops/index.html) | 用退出条件和显式路由控制图的下一步 |
| 11 | [[codex] 异步并行、汇合屏障与 Send](11-codex-parallel-send/index.html) | 从固定分支走到动态任务分发并验证汇总结果 |
| 12 | [[codex] 工具闭环与模型上下文](12-codex-tool-loop/index.html) | 先验证真实工具执行再替换模型决策节点 |
| 13 | [[codex] 人工审批与跨进程恢复](13-codex-interrupt-persistence/index.html) | 从内存中断到 SQLite 保存与恢复暂停任务 |
| 14 | [[codex] 重试策略与业务幂等](14-codex-retry-idempotency/index.html) | 通过提交后超时实验理解重复执行与唯一键 |
| 15 | [[codex] 子图封装与结构化校验](15-codex-subgraphs-validation/index.html) | 设计子图数据边界并为输出修复设置终止条件 |

</div>

## 建议阅读顺序

01–07 是原有基础教程；08–15 是标题带 `[codex]` 的实战补充，按状态更新、数据生命周期、路由、并行、工具循环、恢复、幂等与封装逐步深入。

先读 [08：最小实验](08-codex-state-reducers-stream/index.html) 建立运行环境。文章内的实验编号沿用练习包 01–22，与文章编号不同。每课先预测状态，再运行，再只改一个变量；22 个实验的完整代码、运行命令和预期结果均直接展开在对应文章中，可以复制到自己的练习目录运行，不依赖原始资料目录。

## 前置知识

- 读过 [Agent Basic](../learn-agent-basic/index.html) 或者知道什么是 Agent、Tool Calling
- 会写基本的 Python，知道 `TypedDict` 是什么
- 不需要 LangGraph 经验

## 从哪里开始

如果完全没接触过 LangGraph，从 [第 01 篇](01-what-is-langgraph/index.html) 开始读。

如果已经知道 LangGraph 是状态图，想直接上手，从 [第 02 篇](02-state-node-graph/index.html) 开始。
