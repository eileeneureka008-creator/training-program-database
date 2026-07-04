"""跨校对比 API 路由"""
from fastapi import APIRouter, Query
from src.config import DATABASE_URL
from src.database.models import get_session
from src.queries.cross_compare import (
    compare_major_courses, compare_credits, compare_course_structure, list_common_courses
)

router = APIRouter()


def db():
    return get_session(DATABASE_URL)


@router.get("/compare/courses")
def api_compare_courses(major_name: str = Query(..., description="专业名称，如：金融学")):
    """对比两校相同专业的课程设置异同"""
    session = db()
    try:
        result = compare_major_courses(session, major_name)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/compare/credits")
def api_compare_credits(major_name: str = Query(..., description="专业名称")):
    """对比两校同一专业的总学分要求"""
    session = db()
    try:
        result = compare_credits(session, major_name)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/compare/structure")
def api_compare_structure(major_name: str = Query(..., description="专业名称")):
    """对比两校同一专业的课程结构"""
    session = db()
    try:
        result = compare_course_structure(session, major_name)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/compare/common-courses")
def api_common_courses(major_name: str = Query(..., description="专业名称")):
    """列出两校共同课程"""
    session = db()
    try:
        result = list_common_courses(session, major_name)
        return {"status": "ok", "data": result}
    finally:
        session.close()
