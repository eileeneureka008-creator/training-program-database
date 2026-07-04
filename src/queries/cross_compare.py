"""跨校对比查询模块"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import (
    University, School, Major, Course, MajorCourse
)


def _get_major_info(session: Session, major_name: str, uni_short: str):
    """获取指定大学和专业的 major 对象"""
    uni = session.query(University).filter_by(short_name=uni_short).first()
    if not uni:
        return None, None
    major = (
        session.query(Major)
        .join(School, Major.school_id == School.id)
        .filter(School.university_id == uni.id, Major.name == major_name)
        .first()
    )
    return uni, major


def compare_major_courses(session: Session, major_name: str) -> dict:
    """对比两校相同专业的课程设置异同"""
    _, swufe_major = _get_major_info(session, major_name, "SWUFE")
    _, sufe_major = _get_major_info(session, major_name, "SUFE")

    if not swufe_major:
        return {"error": f"西南财经大学未找到专业: {major_name}"}
    if not sufe_major:
        return {"error": f"上海财经大学未找到专业: {major_name}"}

    def get_courses(major_id):
        return (
            session.query(Course.name, Course.credits, MajorCourse.is_required, MajorCourse.category)
            .join(MajorCourse, Course.id == MajorCourse.course_id)
            .filter(MajorCourse.major_id == major_id)
            .all()
        )

    swufe_courses = {c.name: c for c in get_courses(swufe_major.id)}
    sufe_courses = {c.name: c for c in get_courses(sufe_major.id)}

    common = set(swufe_courses.keys()) & set(sufe_courses.keys())
    only_swufe = set(swufe_courses.keys()) - set(sufe_courses.keys())
    only_sufe = set(sufe_courses.keys()) - set(swufe_courses.keys())

    return {
        "major_name": major_name,
        "swufe_info": {"university": "西南财经大学", "total_credits": swufe_major.total_credits, "course_count": len(swufe_courses)},
        "sufe_info": {"university": "上海财经大学", "total_credits": sufe_major.total_credits, "course_count": len(sufe_courses)},
        "common_courses": [
            {"name": name, "swufe_credits": swufe_courses[name].credits, "sufe_credits": sufe_courses[name].credits}
            for name in sorted(common)
        ],
        "only_swufe": sorted(only_swufe),
        "only_sufe": sorted(only_sufe),
        "common_count": len(common),
        "swufe_only_count": len(only_swufe),
        "sufe_only_count": len(only_sufe),
    }


def compare_credits(session: Session, major_name: str) -> dict:
    """对比两校同一专业的总学分要求"""
    _, swufe_major = _get_major_info(session, major_name, "SWUFE")
    _, sufe_major = _get_major_info(session, major_name, "SUFE")

    result = {"major_name": major_name, "comparisons": []}

    # 西南财经大学
    if swufe_major:
        required = (
            session.query(func.coalesce(func.sum(Course.credits), 0))
            .join(MajorCourse, Course.id == MajorCourse.course_id)
            .filter(MajorCourse.major_id == swufe_major.id, MajorCourse.is_required == True)
            .scalar()
        )
        elective = (
            session.query(func.coalesce(func.sum(Course.credits), 0))
            .join(MajorCourse, Course.id == MajorCourse.course_id)
            .filter(MajorCourse.major_id == swufe_major.id, MajorCourse.is_required == False)
            .scalar()
        )
        result["comparisons"].append({
            "university": "西南财经大学",
            "total_credits": swufe_major.total_credits,
            "required_credits": float(required),
            "elective_credits": float(elective),
        })
    else:
        result["comparisons"].append({"university": "西南财经大学", "error": "未找到该专业"})

    # 上海财经大学
    if sufe_major:
        required = (
            session.query(func.coalesce(func.sum(Course.credits), 0))
            .join(MajorCourse, Course.id == MajorCourse.course_id)
            .filter(MajorCourse.major_id == sufe_major.id, MajorCourse.is_required == True)
            .scalar()
        )
        elective = (
            session.query(func.coalesce(func.sum(Course.credits), 0))
            .join(MajorCourse, Course.id == MajorCourse.course_id)
            .filter(MajorCourse.major_id == sufe_major.id, MajorCourse.is_required == False)
            .scalar()
        )
        result["comparisons"].append({
            "university": "上海财经大学",
            "total_credits": sufe_major.total_credits,
            "required_credits": float(required),
            "elective_credits": float(elective),
        })
    else:
        result["comparisons"].append({"university": "上海财经大学", "error": "未找到该专业"})

    if len(result["comparisons"]) == 2 and "error" not in result["comparisons"][0] and "error" not in result["comparisons"][1]:
        diff = result["comparisons"][0]["total_credits"] - result["comparisons"][1]["total_credits"]
        result["credit_difference"] = f"{diff:+.1f} (西财 - 上财)"

    return result


def compare_course_structure(session: Session, major_name: str) -> dict:
    """对比两校课程结构（按类别统计）"""
    _, swufe_major = _get_major_info(session, major_name, "SWUFE")
    _, sufe_major = _get_major_info(session, major_name, "SUFE")

    def get_category_distribution(major_id):
        return (
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

    result = {"major_name": major_name, "swufe": {}, "sufe": {}}

    if swufe_major:
        for cat, cnt, cred in get_category_distribution(swufe_major.id):
            result["swufe"][cat] = {"course_count": cnt, "credits": float(cred)}
    if sufe_major:
        for cat, cnt, cred in get_category_distribution(sufe_major.id):
            result["sufe"][cat] = {"course_count": cnt, "credits": float(cred)}

    return result


def list_common_courses(session: Session, major_name: str) -> dict:
    """列出两校相同专业的共同课程（相似课程名）"""
    _, swufe_major = _get_major_info(session, major_name, "SWUFE")
    _, sufe_major = _get_major_info(session, major_name, "SUFE")

    if not swufe_major or not sufe_major:
        return {"error": "需要两校都存在该专业"}

    swufe_courses = (
        session.query(Course.name, Course.credits, Course.code)
        .join(MajorCourse, Course.id == MajorCourse.course_id)
        .filter(MajorCourse.major_id == swufe_major.id)
        .all()
    )
    sufe_courses = (
        session.query(Course.name, Course.credits, Course.code)
        .join(MajorCourse, Course.id == MajorCourse.course_id)
        .filter(MajorCourse.major_id == sufe_major.id)
        .all()
    )

    swufe_names = {c.name for c in swufe_courses}
    sufe_names = {c.name for c in sufe_courses}
    common_names = swufe_names & sufe_names

    return {
        "major_name": major_name,
        "common_courses": [
            {"name": name, "swufe_credits": next(c.credits for c in swufe_courses if c.name == name),
             "sufe_credits": next(c.credits for c in sufe_courses if c.name == name)}
            for name in sorted(common_names)
        ],
        "common_count": len(common_names),
        "total_swufe": len(swufe_names),
        "total_sufe": len(sufe_names),
    }
