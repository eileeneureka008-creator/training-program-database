"""基本查询模块：实现 6 项核心查询功能"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import (
    University, School, Major, Course, MajorCourse, CultivationPlan
)


def get_required_courses(session: Session, major_id: int) -> list[dict]:
    """查询某专业的必修课列表"""
    results = (
        session.query(Course, MajorCourse)
        .join(MajorCourse, Course.id == MajorCourse.course_id)
        .filter(
            MajorCourse.major_id == major_id,
            MajorCourse.is_required == True
        )
        .order_by(MajorCourse.semester, Course.name)
        .all()
    )
    return [
        {
            "code": c.code,
            "name": c.name,
            "credits": c.credits,
            "hours_total": c.hours_total,
            "semester": mc.semester,
            "category": mc.category,
        }
        for c, mc in results
    ]


def get_course_info(session: Session, course_id: int = None, course_code: str = None) -> dict:
    """查询某门课程的学分、学时信息"""
    if course_id:
        course = session.query(Course).filter_by(id=course_id).first()
    elif course_code:
        course = session.query(Course).filter_by(code=course_code).first()
    else:
        return None

    if not course:
        return None

    return {
        "code": course.code,
        "name": course.name,
        "name_en": course.name_en,
        "credits": course.credits,
        "hours_theory": course.hours_theory,
        "hours_practice": course.hours_practice,
        "hours_total": course.hours_total,
        "course_type": course.course_type,
        "description": course.description,
    }


def get_total_credits(session: Session, major_id: int) -> dict:
    """查询某专业的总学分要求"""
    major = session.query(Major).filter_by(id=major_id).first()
    if not major:
        return None

    # 统计各类课程的学分
    required_credits = (
        session.query(func.coalesce(func.sum(Course.credits), 0))
        .join(MajorCourse, Course.id == MajorCourse.course_id)
        .filter(MajorCourse.major_id == major_id, MajorCourse.is_required == True)
        .scalar()
    )
    elective_credits = (
        session.query(func.coalesce(func.sum(Course.credits), 0))
        .join(MajorCourse, Course.id == MajorCourse.course_id)
        .filter(MajorCourse.major_id == major_id, MajorCourse.is_required == False)
        .scalar()
    )

    # 按类别统计
    category_stats = (
        session.query(
            MajorCourse.category,
            func.count(Course.id),
            func.coalesce(func.sum(Course.credits), 0)
        )
        .join(MajorCourse, Course.id == MajorCourse.course_id)
        .filter(MajorCourse.major_id == major_id)
        .group_by(MajorCourse.category)
        .all()
    )

    return {
        "major_name": major.name,
        "total_credits_required": major.total_credits,
        "required_credits_sum": float(required_credits),
        "elective_credits_sum": float(elective_credits),
        "category_breakdown": [
            {"category": cat, "course_count": cnt, "credits": float(cred)}
            for cat, cnt, cred in category_stats
        ],
    }


def get_majors_by_course(session: Session, course_id: int = None, course_code: str = None) -> list[dict]:
    """查询开设某门课程的所有专业"""
    if course_id:
        course = session.query(Course).filter_by(id=course_id).first()
    elif course_code:
        course = session.query(Course).filter_by(code=course_code).first()
    else:
        return []

    if not course:
        return []

    results = (
        session.query(Major, School, University, MajorCourse)
        .join(MajorCourse, Major.id == MajorCourse.major_id)
        .join(School, Major.school_id == School.id)
        .join(University, School.university_id == University.id)
        .filter(MajorCourse.course_id == course.id)
        .all()
    )

    return [
        {
            "major_name": m.name,
            "school_name": s.name,
            "university_name": u.name,
            "is_required": mc.is_required,
            "semester": mc.semester,
        }
        for m, s, u, mc in results
    ]


def get_school_plans_overview(session: Session, school_id: int) -> dict:
    """查询某学院下所有专业的培养方案概览"""
    school = session.query(School).filter_by(id=school_id).first()
    if not school:
        return None

    university = session.query(University).filter_by(id=school.university_id).first()
    majors = session.query(Major).filter_by(school_id=school_id).all()

    overview = []
    for major in majors:
        required_count = (
            session.query(func.count())
            .select_from(MajorCourse)
            .filter(MajorCourse.major_id == major.id, MajorCourse.is_required == True)
            .scalar()
        )
        elective_count = (
            session.query(func.count())
            .select_from(MajorCourse)
            .filter(MajorCourse.major_id == major.id, MajorCourse.is_required == False)
            .scalar()
        )
        overview.append({
            "major_name": major.name,
            "code": major.code,
            "degree_type": major.degree_type,
            "duration": major.duration,
            "total_credits": major.total_credits,
            "required_courses_count": required_count,
            "elective_courses_count": elective_count,
        })

    return {
        "school_name": school.name,
        "university_name": university.name if university else "",
        "majors": overview,
    }


def search_courses(session: Session, keyword: str) -> list[dict]:
    """关键词模糊搜索课程名称"""
    pattern = f"%{keyword}%"
    results = (
        session.query(Course)
        .filter(
            (Course.name.like(pattern)) | (Course.name_en.like(pattern))
        )
        .all()
    )
    return [
        {
            "code": c.code,
            "name": c.name,
            "name_en": c.name_en,
            "credits": c.credits,
            "hours_total": c.hours_total,
            "course_type": c.course_type,
        }
        for c in results
    ]


def get_all_schools(session: Session) -> list[dict]:
    """获取所有学院列表"""
    results = (
        session.query(School, University)
        .join(University, School.university_id == University.id)
        .all()
    )
    return [
        {"id": s.id, "name": s.name, "university_name": u.name, "university_id": u.id}
        for s, u in results
    ]


def get_all_majors(session: Session) -> list[dict]:
    """获取所有专业列表"""
    results = (
        session.query(Major, School, University)
        .join(School, Major.school_id == School.id)
        .join(University, School.university_id == University.id)
        .all()
    )
    return [
        {"id": m.id, "name": m.name, "code": m.code, "school_name": s.name, "university_name": u.name}
        for m, s, u in results
    ]
