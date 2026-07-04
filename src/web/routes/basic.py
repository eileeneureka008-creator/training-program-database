"""基础查询 API 路由"""
from fastapi import APIRouter, Query
from src.config import DATABASE_URL
from src.database.models import get_session
from src.queries.basic import (
    get_required_courses, get_course_info, get_total_credits,
    get_majors_by_course, get_school_plans_overview, search_courses,
    get_all_schools, get_all_majors
)

router = APIRouter()


def db():
    return get_session(DATABASE_URL)


@router.get("/majors/{major_id}/required-courses")
def api_required_courses(major_id: int):
    """查询某专业的必修课列表"""
    session = db()
    try:
        result = get_required_courses(session, major_id)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/courses/search")
def api_search_courses(keyword: str = Query(..., description="搜索关键词")):
    """关键词模糊搜索课程名称"""
    session = db()
    try:
        result = search_courses(session, keyword)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/courses/{course_id}/info")
def api_course_info(course_id: int):
    """查询某门课程的学分、学时信息"""
    session = db()
    try:
        result = get_course_info(session, course_id=course_id)
        if not result:
            return {"status": "error", "message": "课程不存在"}
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/courses/{course_id}/majors")
def api_majors_by_course(course_id: int):
    """查询开设某门课程的所有专业"""
    session = db()
    try:
        result = get_majors_by_course(session, course_id=course_id)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/majors/{major_id}/total-credits")
def api_total_credits(major_id: int):
    """查询某专业的总学分要求"""
    session = db()
    try:
        result = get_total_credits(session, major_id)
        if not result:
            return {"status": "error", "message": "专业不存在"}
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/schools/{school_id}/plans-overview")
def api_school_plans(school_id: int):
    """查询某学院下所有专业的培养方案概览"""
    session = db()
    try:
        result = get_school_plans_overview(session, school_id)
        if not result:
            return {"status": "error", "message": "学院不存在"}
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/schools")
def api_all_schools():
    """获取所有学院列表"""
    session = db()
    try:
        result = get_all_schools(session)
        return {"status": "ok", "data": result}
    finally:
        session.close()


@router.get("/majors")
def api_all_majors():
    """获取所有专业列表"""
    session = db()
    try:
        result = get_all_majors(session)
        return {"status": "ok", "data": result}
    finally:
        session.close()
