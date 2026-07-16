# 🧠 Operational Agent Lab (Backend)

基于多智能体协作架构的工业级 AI Agent 学习实验室。该系统模拟了一个真实的“智能旅游助手”场景，涵盖了从单体 ReAct 循环到多智能体编排的核心工程实践。

## 🚀 核心特性

- **多智能体协作 (Multi-Agent Orchestration)**: 采用经理 (Manager) - 专家 (Specialists) 架构，职责清晰，解耦复杂任务。
- **并行执行优化 (Parallel Execution)**: 使用 `ThreadPoolExecutor` 并行调度多个专家 Agent，显著降低端到端响应延迟。
- **可观测性 (Observability)**: 实时记录推理轨迹 (`trace`)、采集证据链 (`evidence`)，并监控 Token 消耗及估算成本。
- **审计与护栏 (Critic & Guardrails)**: 引入独立的审计员 Agent 对输出结果进行逻辑校验，确保建议与客观事实一致。
- **RAG 集成**: 接入 ChromaDB 向量数据库，支持基于语义的旅游攻略检索。

## 🛠️ 技术栈

- **Core**: Python 3.10+, FastAPI
- **LLM**: DeepSeek-V3 / OpenAI GPT-4o
- **Vector DB**: ChromaDB
- **Embedding**: Sentence-Transformers (Multi-lingual)
- **Concurrency**: Python `concurrent.futures`

## 🏃 快速开始

1. **环境准备**:
   ```powershell
   cd agent-lab
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **环境变量配置**:
   复制 `.env.example` 为 `.env` 并填写你的 API Key。

3. **启动服务**:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

## 📖 学习路线图

- **Phase 1-3**: 环境搭建、LLM 接入、RAG 向量检索实现。
- **Phase 4**: 多智能体并行协作、审计护栏与成本监控（当前阶段）。
- **Phase 5**: 计划中 - 使用 LangGraph 进行图形化状态机重构。

---
> 💡 配合 [Agent Lab Frontend](https://github.com/jackmarshh/agent-lab-frontend) 使用可获得仿 Codex 的沉浸式交互体验。
