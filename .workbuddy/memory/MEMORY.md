# agent-lab 项目笔记

## 用户背景
- 之前从事 AI 对话相关工作：Prompt Engineering、多模型加载、RAG
- 计划基于此项目系统学习 AI Agent

## 运行方式
- 默认模式：`AGENT_MODE=demo`，无需 API Key，模板响应
- DeepSeek 模式：设环境变量 `OPENAI_BASE_URL=https://api.deepseek.com/v1`、`OPENAI_MODEL=deepseek-chat`、`AGENT_MODE=openai`，配 API Key
- 启动：`uvicorn app.main:app --reload` (端口 8000)
- 受管 Python venv：`C:\Users\Lenovo\.workbuddy\binaries\python\envs\default`

## 项目结构
- `app/main.py` - FastAPI 入口，`/health` 和 `/diagnose` 两个端点
- `app/agent.py` - Agent 核心循环：Perceive → Reason → Act
- `app/tools.py` - 只读诊断工具（健康检查、日志解析、上游依赖检查）
- `app/models.py` - Pydantic 模型定义
- `sample_logs/` - 示例日志
- `tests/test_api.py` - API 测试
