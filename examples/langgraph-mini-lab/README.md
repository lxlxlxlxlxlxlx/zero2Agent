# LangGraph 最小实验维护基线

本目录包含 21 个主练习和 1 个真实模型选学例子。

教学文章已直接展开全部 22 个实验代码、运行命令与预期结果；读者无需取得本目录或原始资料。课程入口见 [LangGraph 实验课](../../learn-langgraph-lab/index.md)。页面代码经过最小化整理，与本目录保留的原包示例在节点数量上可能不同；两套代码分别验证。

以下命令供维护者在仓库内执行回归验证：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-sqlite.txt
python check_syntax.py
python run_all.py --sqlite
```

fish 使用 `source .venv/bin/activate.fish`。所有命令在本目录运行。

核心基线为 LangGraph 1.2.12。主练习已在 Python 3.11.12 下全部通过；真实模型例子未运行，不计入自测结果。

## 原包编号与课程对应

| 原包编号 | 新课程 |
|---|---|
| 01 | [01 State：节点只交回变化的字段](../../learn-langgraph-lab/01-state-updates/index.md) |
| 02 | [02 Reducer：列表为什么会重复](../../learn-langgraph-lab/02-reducers/index.md) |
| 03 | [03 消息 ID：追加一条还是修订一条](../../learn-langgraph-lab/03-message-ids/index.md) |
| 04 | [06 状态流：看更新还是看完整快照](../../learn-langgraph-lab/06-state-streaming/index.md) |
| 05 | [14 Checkpointer：同一会话延续，不同会话隔离](../../learn-langgraph-lab/14-checkpoint-threads/index.md) |
| 06 | [13 Runtime Context：把运行依赖与状态分开](../../learn-langgraph-lab/13-runtime-context/index.md) |
| 07 | [18 RetryPolicy：只重试可恢复的错误](../../learn-langgraph-lab/18-retry-policy/index.md) |
| 08 | [04 条件边：让状态决定下一步](../../learn-langgraph-lab/04-conditional-routing/index.md) |
| 09 | [05 循环：把停止条件写进图](../../learn-langgraph-lab/05-bounded-loops/index.md) |
| 10 | [08 异步节点：把等待时间重叠起来](../../learn-langgraph-lab/08-async-nodes/index.md) |
| 11 | [11 工具闭环：请求、执行、结果回填](../../learn-langgraph-lab/11-tool-loop/index.md) |
| 12 | [16 Interrupt：等待审批，再继续执行](../../learn-langgraph-lab/16-interrupt-resume/index.md) |
| 13 | [15 Store：跨会话读取同一份用户资料](../../learn-langgraph-lab/15-store-memory/index.md) |
| 14 | [12 模型上下文：历史保存多少，本轮发送多少](../../learn-langgraph-lab/12-model-context/index.md) |
| 15 | [07 汇合屏障：等两个分支都完成](../../learn-langgraph-lab/07-fan-in/index.md) |
| 16 | [09 Send：按输入数量分发任务](../../learn-langgraph-lab/09-dynamic-send/index.md) |
| 17 | [10 Command：更新状态并选择后继](../../learn-langgraph-lab/10-command-routing/index.md) |
| 18 | [20 子图：隐藏内部步骤，保留数据接口](../../learn-langgraph-lab/20-subgraphs/index.md) |
| 19 | [21 结构化校验：合法 JSON 也可能不合格](../../learn-langgraph-lab/21-structured-validation/index.md) |
| 20 | [17 SQLite：退出程序后恢复暂停任务](../../learn-langgraph-lab/17-sqlite-resume/index.md) |
| 21 | [19 幂等：提交后超时，重试会不会重复写入](../../learn-langgraph-lab/19-idempotency/index.md) |
| 22 | [22 接入真实模型：只替换决策节点](../../learn-langgraph-lab/22-real-model/index.md) |
