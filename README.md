# Operational Agent Lab

一个可运行的 Agent 学习骨架：接收告警、运行**只读**诊断工具、基于证据生成建议，并返回可审计的执行轨迹。

## 运行

```powershell
cd agent-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开 `http://127.0.0.1:8000/docs`，或调用：

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/diagnose -ContentType 'application/json' -Body '{"service":"payments-api","incident":"503 rate is rising"}'
```

默认 `AGENT_MODE=demo`，无需 API Key，便于先理解 Agent 的执行链路。

## 启用 OpenAI

在 shell 中设置密钥与模型：

```powershell
$env:OPENAI_API_KEY = '...'
$env:OPENAI_MODEL = 'gpt-4.1-mini'
$env:AGENT_MODE = 'openai'
```

模型模式仍先执行只读工具，再把工具证据交给模型。真实环境中把 `app/tools.py` 替换为日志、指标和 Runbook 查询；将任何写操作置于显式人工审批之后。

## 学习顺序

1. 阅读 `app/agent.py`：理解「任务 → 工具 → 证据 → 建议」的最小闭环。
2. 在 `app/tools.py` 新增一个只读工具，并把它的证据接入 Agent。
3. 给 `tests/` 增加失败和边界场景。
4. 再引入 RAG、任务持久化、追踪和人工审批；不要急着拆多 Agent。

## 验证

```powershell
pytest -q
```
