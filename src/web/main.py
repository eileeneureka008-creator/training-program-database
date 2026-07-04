"""FastAPI 主入口"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import DATABASE_URL, BASE_DIR
from src.database.models import get_session
from src.web.routes import basic, compare, nl_query

app = FastAPI(
    title="培养方案数据库系统",
    description="西南财经大学 & 上海财经大学 培养方案查询与跨校对比系统",
    version="1.0.0",
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.include_router(basic.router, prefix="/api", tags=["基础查询"])
app.include_router(compare.router, prefix="/api", tags=["跨校对比"])
app.include_router(nl_query.router, prefix="/api", tags=["自然语言查询"])


@app.on_event("startup")
def startup_seed():
    """首次启动时自动建库并导入数据"""
    db_path = os.path.join(BASE_DIR, "data", "cultivation.db")
    if not os.path.exists(db_path):
        from src.database.seed import seed_all
        seed_all()


def get_db():
    return get_session(DATABASE_URL)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/majors")
async def page_majors(request: Request):
    return templates.TemplateResponse("major.html", {"request": request})


@app.get("/courses")
async def page_courses(request: Request):
    return templates.TemplateResponse("course.html", {"request": request})


@app.get("/schools")
async def page_schools(request: Request):
    return templates.TemplateResponse("school.html", {"request": request})


@app.get("/compare")
async def page_compare(request: Request):
    return templates.TemplateResponse("compare.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
