---
layout: default
title: "LangGraph 实验课"
description: "一课一个机制，用最小完整代码学会状态、路由、工具、记忆与恢复"
eyebrow: "LangGraph Lab"
---

# LangGraph 实验课

会连节点，不代表能解释历史为什么重复、任务为何恢复不了、重试为何写入两次。本模块把这些问题拆成 22 节短课，每节只验证一个核心机制。

先看问题，再读最小代码，预测结果后运行，最后只改一个地方。前 21 课不需要模型服务，第 22 课选学接入真实模型。全部代码直接写在页面中，复制单课即可运行，不依赖原始资料目录或配套下载。

## 如何学

1. 先读[第 01 课的环境准备](01-state-updates/index.html)，使用同一个 Python 虚拟环境。
2. 一次只复制一课，按页面给出的文件名保存，保留示例末尾的断言。
3. 运行后对照输出，解释是哪一个字段、节点或条件决定了结果。
4. 完成“动手改一处”，同步修改对应断言，再观察结果是否符合预测。

每课依次给出问题、机制、完整代码、结果解读、三处关键代码、修改练习和常见错误。代码量保持在 23–59 行，不为日志、格式化或包装增加与当前知识点无关的节点。

如果还不熟悉图、节点和边，先读原有的 [LangGraph 基础模块](../learn-langgraph/index.html)。本模块专门承接这些实验课程与后续新增练习，标题使用知识点名称。

## 课程目录

### 一、状态怎样流动

- **01** [State：节点只交回变化的字段](01-state-updates/index.html)：用两个节点看清状态读取与局部更新。
- **02** [Reducer：列表为什么会重复](02-reducers/index.html)：对比覆盖字段与追加字段的更新规则。
- **03** [消息 ID：追加一条还是修订一条](03-message-ids/index.html)：用 MessagesState 更新同一条消息。

### 二、下一步由谁决定

- **04** [条件边：让状态决定下一步](04-conditional-routing/index.html)：分离状态更新与条件路由职责。
- **05** [循环：把停止条件写进图](05-bounded-loops/index.html)：用回边与次数保护控制重复执行。
- **06** [状态流：看更新还是看完整快照](06-state-streaming/index.html)：区分 updates 与 values 的观察视角。

### 三、并行任务怎样汇合

- **07** [汇合屏障：等两个分支都完成](07-fan-in/index.html)：用不同字段隔离并行结果并明确汇合。
- **08** [异步节点：把等待时间重叠起来](08-async-nodes/index.html)：用 ainvoke 与 astream 驱动异步分支。
- **09** [Send：按输入数量分发任务](09-dynamic-send/index.html)：让一个 worker 节点接收多份独立输入。
- **10** [Command：更新状态并选择后继](10-command-routing/index.html)：在一个返回值里表达更新与跳转。

### 四、工具与上下文

- **11** [工具闭环：请求、执行、结果回填](11-tool-loop/index.html)：用固定模型决策跑通真实工具调用。
- **12** [模型上下文：历史保存多少，本轮发送多少](12-model-context/index.html)：把保留的消息与本轮输入分开管理。
- **13** [Runtime Context：把运行依赖与状态分开](13-runtime-context/index.html)：通过 context 注入本轮配置。

### 五、记忆、暂停与恢复

- **14** [Checkpointer：同一会话延续，不同会话隔离](14-checkpoint-threads/index.html)：用 thread_id 找回已有图状态。
- **15** [Store：跨会话读取同一份用户资料](15-store-memory/index.html)：通过命名空间与 key 组织长期资料。
- **16** [Interrupt：等待审批，再继续执行](16-interrupt-resume/index.html)：观察暂停点与恢复时的节点重入。
- **17** [SQLite：退出程序后恢复暂停任务](17-sqlite-resume/index.html)：用四次独立进程验证检查点落盘。

### 六、失败处理与复用

- **18** [RetryPolicy：只重试可恢复的错误](18-retry-policy/index.html)：限制异常类型与总尝试次数。
- **19** [幂等：提交后超时，重试会不会重复写入](19-idempotency/index.html)：用稳定业务键约束重复请求的结果。
- **20** [子图：隐藏内部步骤，保留数据接口](20-subgraphs/index.html)：通过共享字段组合父图与子图。
- **21** [结构化校验：合法 JSON 也可能不合格](21-structured-validation/index.html)：对输出加约束并限制修复次数。

### 七、选学：接入真实模型

- **22** [接入真实模型：只替换决策节点](22-real-model/index.html)：将确定性工具闭环换成模型驱动。

## 验收清单

- 状态：能说明覆盖、追加、按消息 ID 更新各自适用什么场景。
- 路由：能预测一份输入走哪条边，解释循环何时结束。
- 并行：能指出每个分支写哪个字段，汇合节点在等谁。
- 工具：能沿 human → ai → tool → ai 验证调用与回填。
- 记忆：能区分 State、Runtime Context、Checkpointer 与 Store。
- 恢复：能关掉程序，再通过同一 SQLite 文件和 thread_id 继续任务。
- 可靠性：能解释重试次数、去重键和结构化校验失败出口。

## 运行基线

2026-10-08 使用 Python 3.11.12、LangGraph 1.2.12、langchain-core 1.6.7、Pydantic 2.13.5 验证。第 17 课另使用 langgraph-checkpoint-sqlite 3.1.1。页面按默认 v1 状态流格式解释输出。

前 21 课的页面代码逐课提取到临时目录独立运行，并核对断言与预期输出；第 17 课另外经过四个独立进程验证。第 22 课仅做语法检查，未连接真实模型服务。

下一篇建议继续看：

- [State：节点只交回变化的字段](01-state-updates/index.html)
