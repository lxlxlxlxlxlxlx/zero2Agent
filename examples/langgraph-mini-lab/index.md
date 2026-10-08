---
layout: default
title: "[codex] LangGraph 实验阅读地图"
description: "22 个实验的完整代码均在教学页面展开"
eyebrow: "LangGraph / Lab"
---

# [codex] LangGraph 实验阅读地图

本系列的 21 个主练习与 1 个真实模型选学例子，都已经完整展开在对应文章中。每个实验包括全部 Python 代码、保存文件名、运行命令和预期输出；选学模型例子注明输出不固定。

从任意文章开始，按页面中的安装命令准备环境，再复制代码到自己的练习目录即可。教程不依赖原始 `langgraph_mini_lab` 目录，不需要下载配套源码。仓库中的 Python 文件用于维护和回归验证，阅读与练习不要求取得这些文件。

## 按问题选择文章

| 教学文章 | 页面内的完整实验 |
|---|---|
| [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html) | 01 状态与局部更新、02 覆盖与追加的区别、03 消息按 ID 更新、04 节点更新与完整状态流 |
| [[codex] State、Context 与跨会话记忆](../../learn-langgraph/09-codex-context-memory/index.html) | 05 会话状态与 thread_id、06 运行时上下文、13 跨会话记忆 |
| [[codex] 条件路由、循环与 Command](../../learn-langgraph/10-codex-routing-loops/index.html) | 08 条件分支、09 回边与退出条件、17 Command 更新并跳转 |
| [[codex] 异步并行、汇合屏障与 Send](../../learn-langgraph/11-codex-parallel-send/index.html) | 10 异步并行与等待汇总、15 四节点菱形汇总、16 Send 动态分发 |
| [[codex] 工具闭环与模型上下文](../../learn-langgraph/12-codex-tool-loop/index.html) | 11 工具调用闭环（模拟模型）、14 保存历史不等于全部发送给模型、22 真实模型工具闭环（选学） |
| [[codex] 人工审批与跨进程恢复](../../learn-langgraph/13-codex-interrupt-persistence/index.html) | 12 人工审批与恢复、20 SQLite 跨进程恢复 |
| [[codex] 重试策略与业务幂等](../../learn-langgraph/14-codex-retry-idempotency/index.html) | 07 节点自动重试、21 重试时避免重复写入 |
| [[codex] 子图封装与结构化校验](../../learn-langgraph/15-codex-subgraphs-validation/index.html) | 18 子图封装与共享字段、19 结构化校验与一次修复 |

## 本次验证记录

2026-10-08，在 macOS、Python 3.11.12 下验证。实际解析的关键依赖为 LangGraph 1.2.12、langchain-core 1.6.7、Pydantic 2.13.5、langgraph-checkpoint-sqlite 3.1.1。

| 验证层 | 本次结果 | 证据范围 |
|---|---|---|
| Python 语法与静态图结构 | 24 个 Python 文件、22 个示例通过 | 包括 22 个示例与 2 个原有检查脚本；不能单独证明图能运行 |
| 真实 LangGraph 整图运行 | 21 通过，0 失败，0 跳过 | compile、状态合并、路由、异步、工具执行、检查点、人工中断与恢复 |
| SQLite 跨进程恢复 | 通过 | 四个独立 Python 进程共用临时数据库 |
| 页面代码独立运行 | 21 通过 | 从文章正文提取完整代码到临时空目录运行，输出与预期一致，不读取原始资料 |
| 真实模型选学 22 | 未运行 | 需要读者配置实际支持工具调用的模型服务 |

原包在 2026-10-05 仅完成静态与部分节点逻辑检查；以上是本次仓库集成后新执行的结果。确定性示例通过不代表真实模型回答质量、服务并发能力或生产业务验收通过。

## 阅读方式

先预测状态如何变化，再运行原例，最后只改一个输入或规则。各实验保留独立导入、状态定义、节点、连线和入口，不能将多个完整示例直接拼成一个文件。

其中 SQLite 实验会创建自己练习目录下的 `.runtime/lesson20.sqlite`。它是运行时数据；以后删除原始学习资料不影响教程，但不要误删自己尚未完成的暂停任务数据库。

下一篇建议继续看：

- [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html)
