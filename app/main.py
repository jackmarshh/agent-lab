from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.agent import diagnose
from app.models import DiagnoseRequest, DiagnoseResponse

app = FastAPI(title="Operational Agent Lab", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
def diagnose_incident(request: DiagnoseRequest) -> DiagnoseResponse:
    return diagnose(request)
