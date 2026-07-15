# Agent 学习路线图

> 基于 `agent-lab` 项目，从零到主流框架的动手学习路线。
>
> 前提基础：Prompt Engineering / 多模型加载 / RAG

---

## 总览

```
Phase 0  拆解 agent.py  — 理解编排循环
   ↓
Phase 1  Tools 深入     — 新增自定义工具
   ↓
Phase 2  Memory        — 让 Agent 有记忆力
   ↓
Phase 3  RAG 集成      — 把知识塞进 Agent
   ↓
Phase 4  Guardrails    — 安全 + 多 Agent 拆分
   ↓
Phase 5  LangGraph 重构 — 对接主流框架
```

每完成一个 Phase，agent-lab 就朝生产级 Agent 框架进化了一步。

---

## Phase 0 — 逐行拆解 agent.py

**目标：** 彻底理解 Perceive → Reason → Act 编排循环

**具体动作：**
- 逐行过 `app/agent.py`，理解：
  - 为什么工具必须返回结构化证据（`Evidence`）
  - `_demo_response()` 和 OpenAI 分支的流程差异
  - 编排循环如果抽象成接口，应该长什么样
- 结合 `app/tools.py` 看工具是如何被编排循环调用的
- 结合 `app/main.py` 看 HTTP 入口如何接入 Agent

**框架映射：** LangChain 的 `AgentExecutor`、LangGraph 的 `Graph`、OpenAI Agents SDK 的 `Runner` — 都是这个循环的泛化。

**对应代码：**
- `app/main.py` — FastAPI 入口
- `app/agent.py` — 核心编排循环
- `app/tools.py` — 工具层
- `app/models.py` — 数据结构定义

---

## Phase 1 — Tools 深入

**目标：** 理解工具抽象和 Function Calling 原理

**具体动作：**
- 在 `app/tools.py` 新增 2 个真实工具：
  1. `run_sql_query()` — 读取本地 SQLite 数据库，返回查询结果
  2. `search_incident_runbook()` — 在 Markdown 文件中模糊搜索运维手册
- 工具写好 docstring，观察 DeepSeek 模式下的回复质量变化

**关键学到：**
- 工具描述怎么写 LLM 才能正确理解用途
- 工具返回什么格式最利于模型推理
- 这就是 Function Calling 的底层原理

**框架映射：** → LangGraph 的 `@tool` 装饰器 / OpenAI Function Calling

---

## Phase 2 — Memory

**目标：** 让 Agent 具备跨轮对话的记忆能力

**具体动作：**
- `DiagnoseRequest` 加 `conversation_id` 字段
- 在 `agent.py` 里把历史诊断记录拼进 System Prompt（短期记忆）
- 用 SQLite 持久化每次诊断结论（长期记忆）
- 让 Agent 在多次诊断间能引用「上次的结论」

**关键学到：**
- 短期记忆 = context window 管理
- 长期记忆 = 外部存储 + 检索
- 记忆的摘要与裁剪策略

**框架映射：** → LangGraph State 管理

---

## Phase 3 — RAG 集成

**目标：** 把外部知识注入 Agent 的推理过程

**具体动作：**
- 安装 `chromadb`（或先用 JSON 文件模拟向量库）
- 准备运维知识文档并入库
- 封装 `retrieve_knowledge()` 工具，挂到 Agent 的工具列表
- 观察 Agent 在回答中是否引用了知识库内容

**关键学到：**
- RAG 在 Agent 里的角色：就是另一个 Tool
- 检索策略（相似度 / MMR / 混合检索）对 Agent 决策的影响
- 你的 RAG 经验直接迁移

**框架映射：** → LangChain RAG Chain / Dify 知识库

---

## Phase 4 — Guardrails + 多 Agent 拆分

**目标：** 让 Agent 安全可控，并理解多 Agent 协作模式

**具体动作：**
1. **安全层**
   - 输入校验：防止 Prompt Injection
   - 高风险操作审批：如"回滚部署"需要人工确认
   - 输出审核：确保返回内容符合预期格式
2. **多 Agent 拆分**
   - 拆出两个子 Agent：
     - 「日志分析 Agent」— 只读日志
     - 「数据库诊断 Agent」— 只查数据库
   - 主 Agent 协调，子 Agent 各管各的工具

**关键学到：**
- Guardrails 让 Agent 可安全落地生产
- 多 Agent 拆分的边界原则：职责清晰、工具隔离
- 什么时候拆，什么时候不拆

**框架映射：** → CrewAI（角色分工）/ AutoGen（多 Agent 对话）

---

## Phase 5 — LangGraph 重构

**目标：** 用主流框架重写项目，对接生产级 Agent 生态

**具体动作：**
- 安装 `langgraph` + `langchain`
- 用 `StateGraph` 重构核心流程：
  - 工具函数 → 图的节点
  - 条件判断 → 图的边
  - 记忆 → State 持久化
- 接入 LangChain 生态的 Tool 集成、RAG Chain、Memory

**关键学到：**
- 图（Graph）比线性循环强在哪：
  - 条件分支
  - 并行执行
  - 状态持久化
- 走到这一步，你已经能用 LangGraph 写生产级 Agent 了

**框架映射：** → LangGraph / LangChain 生态

---

## 学习原则

1. **动手 > 看书。** 每个 Phase 都改代码、跑测试、看效果。
2. **理解原理 > 记忆 API。** 框架换了一茬又一茬，Perceive→Reason→Act 不会变。
3. **每完成一个 Phase，对比一下当前代码和 Phase 0 的差异。**

## 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [CrewAI 文档](https://docs.crewai.com/)
- [AutoGen 文档](https://microsoft.github.io/autogen/)
- [Dify](https://dify.ai/)
