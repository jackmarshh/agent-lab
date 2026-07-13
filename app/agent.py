import os

from app.models import DiagnoseRequest, DiagnoseResponse, Evidence
from app.tools import check_upstream_dependencies, inspect_service_health, inspect_service_logs


SYSTEM_PROMPT = """You are a cautious production incident assistant. Use only supplied evidence.
Recommend safe, reversible next actions. Do not claim you executed an action.
Return exactly three labelled lines: Summary:, Action:, Status: (completed or needs_attention)."""


def _demo_response(request: DiagnoseRequest, evidence: list[Evidence]) -> DiagnoseResponse:
    pool_errors = sum(1 for e in evidence if "connection pool exhausted" in e.detail)
    error_count = sum(1 for e in evidence if "503" in e.detail or "error" in e.detail.lower())
    db_pool_info = next((e.detail for e in evidence if "connection pool usage" in e.detail), "DB pool status unknown")
    pg_info = next((e.detail for e in evidence if "payment gateway" in e.detail.lower()), "Payment gateway status unknown")
    return DiagnoseResponse(
        status="needs_attention",
        summary=f"Agent inspected {request.service}: collected {len(evidence)} pieces of evidence, found {error_count} error indicators, and {pool_errors} connection-pool exhaustion signals.",
        recommended_action=f"1. {db_pool_info} — increase pool max or throttle {request.service}. 2. {pg_info} — check if slow upstream is holding connections open. 3. Roll back latest deployment only after mitigating pool pressure.",
        evidence=evidence,
        trace=["received incident", "ran read-only health inspection", "ran read-only log inspection", "ran upstream dependency check", "generated evidence-based recommendation"],
    )


def diagnose(request: DiagnoseRequest) -> DiagnoseResponse:
    evidence = [
        *inspect_service_health(request.service),
        *inspect_service_logs(request.service),
        *check_upstream_dependencies(request.service),
    ]
    if os.getenv("AGENT_MODE", "demo").lower() != "openai":
        return _demo_response(request, evidence)

    from openai import OpenAI

    evidence_text = "\n".join(f"- {item.source}: {item.detail}" for item in evidence)
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Incident: {request.incident}\nService: {request.service}\nEvidence:\n{evidence_text}"},
        ],
        temperature=0.1,
    )
    reply = response.choices[0].message.content
    lines = {line.split(":", 1)[0].lower(): line.split(":", 1)[1].strip()
             for line in reply.splitlines() if ":" in line}
    status = "completed" if lines.get("status", "").lower() == "completed" else "needs_attention"
    return DiagnoseResponse(
        status=status,
        summary=lines.get("summary", reply),
        recommended_action=lines.get("action", "Escalate to an on-call engineer for review."),
        evidence=evidence,
        trace=["received incident", "ran read-only health inspection", "ran read-only log inspection", "requested model recommendation"],
    )
