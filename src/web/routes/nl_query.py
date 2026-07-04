"""自然语言查询 API 路由"""
from fastapi import APIRouter
from pydantic import BaseModel
from src.config import DATABASE_URL
from src.database.models import get_session
from src.nl2sql.engine import NL2SQLEngine

router = APIRouter()


class NLQueryRequest(BaseModel):
    query: str


@router.post("/nl-query")
def api_nl_query(req: NLQueryRequest):
    """自然语言查询接口，用户可用中文提问"""
    session = get_session(DATABASE_URL)
    try:
        engine = NL2SQLEngine(session)
        result = engine.execute(req.query)
        return {"status": "ok", "data": result}
    finally:
        session.close()
