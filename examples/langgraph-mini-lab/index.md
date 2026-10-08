---
layout: default
title: "[codex] LangGraph 最小实验配套代码"
description: "21 个确定性主练习与 1 个真实模型选学例子"
eyebrow: "LangGraph / Lab"
---

# [codex] LangGraph 最小实验配套代码

理解一个机制，最好先在只有两到四个节点的图里观察它。本目录将用户提供的 `langgraph_mini_lab` 中的独立示例整理为站点配套代码；教学正文从 [08：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html) 开始。

每个示例自带状态定义、节点、连线和运行入口，主练习保留原包的输出断言与自测脚本。这里的节点数量只指顶层注册的业务节点，不包括 START、END、路由函数和子图内部节点。

## 安装与运行

取得本分支的完整仓库代码后，在仓库根目录执行：

```bash
cd examples/langgraph-mini-lab
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python 02_nodes/01_state_sequence.py
python check_syntax.py
python run_all.py
```

建议 Python 3.11 或以上；fish 用 `source .venv/bin/activate.fish` 激活。主练习安装依赖后不调用外部模型，也不需要 Key。`requirements.txt` 固定 LangGraph 1.2.12，其余依赖用范围约束，不是完整锁文件。

默认自测执行 20 个主练习，SQLite 第 20 课显示 SKIP。覆盖全部 21 个：

```bash
python -m pip install -r requirements-sqlite.txt
python run_all.py --sqlite
```

SQLite 额外依赖固定为 `langgraph-checkpoint-sqlite==3.1.1`。自测用临时数据库分别启动 start、status、resume、status 四个进程，不触碰手工练习的 `.runtime` 数据。

## 实验与文章对应

文章按知识主题组织，文件保留原始实验编号。每次先预测结果，再运行原例，然后只改一个输入或规则。改完也要更新原有断言和预期，避免用旧答案判断新题目。

| 实验 | 源码 | 教学文章 |
|---|---|---|
| 01 | [状态与局部更新](02_nodes/01_state_sequence.py) | [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html) |
| 02 | [覆盖与追加的区别](02_nodes/02_reducer.py) | [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html) |
| 03 | [消息按 ID 更新](02_nodes/03_message_ids.py) | [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html) |
| 04 | [节点更新与完整状态流](02_nodes/04_stream.py) | [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html) |
| 05 | [会话状态与 thread_id](02_nodes/05_checkpoint_threads.py) | [[codex] State、Context 与跨会话记忆](../../learn-langgraph/09-codex-context-memory/index.html) |
| 06 | [运行时上下文](02_nodes/06_runtime_context.py) | [[codex] State、Context 与跨会话记忆](../../learn-langgraph/09-codex-context-memory/index.html) |
| 07 | [节点自动重试](02_nodes/07_retry.py) | [[codex] 重试策略与业务幂等](../../learn-langgraph/14-codex-retry-idempotency/index.html) |
| 08 | [条件分支](03_nodes/08_conditional_edges.py) | [[codex] 条件路由、循环与 Command](../../learn-langgraph/10-codex-routing-loops/index.html) |
| 09 | [回边与退出条件](03_nodes/09_loop.py) | [[codex] 条件路由、循环与 Command](../../learn-langgraph/10-codex-routing-loops/index.html) |
| 10 | [异步并行与等待汇总](03_nodes/10_parallel_async.py) | [[codex] 异步并行、汇合屏障与 Send](../../learn-langgraph/11-codex-parallel-send/index.html) |
| 11 | [工具调用闭环（模拟模型）](03_nodes/11_tool_agent.py) | [[codex] 工具闭环与模型上下文](../../learn-langgraph/12-codex-tool-loop/index.html) |
| 12 | [人工审批与恢复](03_nodes/12_interrupt_resume.py) | [[codex] 人工审批与跨进程恢复](../../learn-langgraph/13-codex-interrupt-persistence/index.html) |
| 13 | [跨会话记忆](03_nodes/13_store_memory.py) | [[codex] State、Context 与跨会话记忆](../../learn-langgraph/09-codex-context-memory/index.html) |
| 14 | [保存历史不等于全部发送给模型](03_nodes/14_model_context.py) | [[codex] 工具闭环与模型上下文](../../learn-langgraph/12-codex-tool-loop/index.html) |
| 15 | [四节点菱形汇总](04_nodes/15_diamond.py) | [[codex] 异步并行、汇合屏障与 Send](../../learn-langgraph/11-codex-parallel-send/index.html) |
| 16 | [Send 动态分发](04_nodes/16_send_map_reduce.py) | [[codex] 异步并行、汇合屏障与 Send](../../learn-langgraph/11-codex-parallel-send/index.html) |
| 17 | [Command 更新并跳转](04_nodes/17_command_route.py) | [[codex] 条件路由、循环与 Command](../../learn-langgraph/10-codex-routing-loops/index.html) |
| 18 | [子图封装与共享字段](04_nodes/18_subgraph.py) | [[codex] 子图封装与结构化校验](../../learn-langgraph/15-codex-subgraphs-validation/index.html) |
| 19 | [结构化校验与一次修复](04_nodes/19_structured_validation.py) | [[codex] 子图封装与结构化校验](../../learn-langgraph/15-codex-subgraphs-validation/index.html) |
| 20 | [SQLite 跨进程恢复](04_nodes/20_sqlite_resume.py) | [[codex] 人工审批与跨进程恢复](../../learn-langgraph/13-codex-interrupt-persistence/index.html) |
| 21 | [重试时避免重复写入](04_nodes/21_idempotency.py) | [[codex] 重试策略与业务幂等](../../learn-langgraph/14-codex-retry-idempotency/index.html) |
| 22 | [真实模型工具闭环](optional/22_real_tool_agent.py) | [[codex] 工具闭环与模型上下文](../../learn-langgraph/12-codex-tool-loop/index.html) |

## 本次验证记录

2026-10-08，在 macOS、Python 3.11.12 下验证。实际解析的关键依赖为 LangGraph 1.2.12、langchain-core 1.6.7、Pydantic 2.13.5、langgraph-checkpoint-sqlite 3.1.1。

| 验证层 | 本次结果 | 证据范围 |
|---|---|---|
| Python 语法与静态图结构 | 24 个 Python 文件、22 个示例通过 | 包括 22 个示例与 2 个原有检查脚本；不能单独证明图能运行 |
| 真实 LangGraph 整图运行 | 21 通过，0 失败，0 跳过 | compile、状态合并、路由、异步、工具执行、检查点、人工中断与恢复 |
| SQLite 跨进程恢复 | 通过 | 四个独立 Python 进程共用临时数据库 |
| 真实模型选学 22 | 未运行 | 需要读者配置实际支持工具调用的模型服务 |

原包在 2026-10-05 仅完成静态与部分节点逻辑检查；以上是本次仓库集成后新执行的结果。确定性示例通过不代表真实模型回答质量、服务并发能力或生产业务验收通过。

## 手工体验进程退出后恢复

在同一个实验目录依次运行：

```bash
python 04_nodes/20_sqlite_resume.py start
python 04_nodes/20_sqlite_resume.py status
python 04_nodes/20_sqlite_resume.py resume
python 04_nodes/20_sqlite_resume.py status
```

数据库默认在 `.runtime/lesson20.sqlite`，也可以通过 `LANGGRAPH_LAB_DATA_DIR` 指定自己的目录。暂停时再次 start 会被拒绝；恢复后 next 从 approve 变为空。所有发布行为都是字符串模拟，不会调用外部发布系统。

## 真实模型选学

```bash
python -m pip install -r requirements-llm.txt
export LLM_MODEL="服务实际提供的模型名"
python optional/22_real_tool_agent.py
```

默认地址是本机 `http://127.0.0.1:8080/v1`。服务需自行运行并支持工具调用；切换服务时设置 `LLM_BASE_URL` 和 `LLM_API_KEY`，不要将 Key 写进文件。示例没有下载或启动模型的功能，也不保证模型一定选择调用工具。

## 范围与来源

本包没有接入 Token 级模型流、向量检索、可观测平台、Web 服务、生产权限系统或分布式事务。示例的内存存储和 SQLite 各有生命周期；业务键和命名空间不自动构成访问控制。

练习代码、manifest 和两个检查脚本来自用户提供的学习包，文章与站点组织为本次改编；外部 API 依据见 [LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/graph-api)。本系列保持默认 v1 返回格式，切换流式 API 版本时需同步更改结果解析。

下一篇建议继续看：

- [[codex] 最小实验：State、Reducer 与状态流](../../learn-langgraph/08-codex-state-reducers-stream/index.html)
