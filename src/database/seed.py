"""数据导入脚本：从 JSON 文件读取样本数据并写入数据库"""
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import DATABASE_URL, SAMPLE_DATA_DIR
from src.database.models import (
    Base, University, School, Major, Course, MajorCourse,
    CultivationPlan, PlanCourseGroup
)


def load_json(filename: str) -> list:
    path = os.path.join(SAMPLE_DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_university(session, name: str, short_name: str) -> University:
    uni = session.query(University).filter_by(name=name).first()
    if not uni:
        uni = University(name=name, short_name=short_name)
        session.add(uni)
        session.flush()
    return uni


def seed_all():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("=== 开始导入数据 ===")

        # 1. 导入大学
        print("[1/6] 导入大学...")
        swufe = seed_university(session, "西南财经大学", "SWUFE")
        sufe = seed_university(session, "上海财经大学", "SUFE")
        uni_map = {"swufe": swufe, "sufe": sufe}

        # 2. 导入学院
        print("[2/6] 导入学院...")
        school_map = {}
        for uni_key, uni_obj in uni_map.items():
            schools_data = load_json(f"{uni_key}_schools.json")
            for s in schools_data:
                school = session.query(School).filter_by(
                    name=s["name"], university_id=uni_obj.id
                ).first()
                if not school:
                    school = School(name=s["name"], university_id=uni_obj.id)
                    session.add(school)
                    session.flush()
                school_map[f"{uni_key}:{s['name']}"] = school

        # 3. 导入专业
        print("[3/6] 导入专业...")
        major_map = {}
        for uni_key, uni_obj in uni_map.items():
            majors_data = load_json(f"{uni_key}_majors.json")
            for m in majors_data:
                school_key = f"{uni_key}:{m['school']}"
                school = school_map.get(school_key)
                if not school:
                    print(f"  警告：找不到学院 {school_key}，跳过专业 {m['name']}")
                    continue
                major = session.query(Major).filter_by(
                    name=m["name"], school_id=school.id
                ).first()
                if not major:
                    major = Major(
                        name=m["name"],
                        code=m.get("code"),
                        school_id=school.id,
                        degree_type=m.get("degree_type", "学士"),
                        duration=m.get("duration", "4年"),
                        total_credits=m.get("total_credits"),
                    )
                    session.add(major)
                    session.flush()
                major_map[f"{uni_key}:{m['name']}"] = major

        # 4. 导入课程
        print("[4/6] 导入课程...")
        course_map = {}
        for uni_key in uni_map:
            courses_data = load_json(f"{uni_key}_courses.json")
            for c in courses_data:
                course = session.query(Course).filter_by(code=c["code"]).first()
                if not course:
                    course = Course(
                        code=c["code"],
                        name=c["name"],
                        name_en=c.get("name_en"),
                        credits=c.get("credits"),
                        hours_theory=c.get("hours_theory"),
                        hours_practice=c.get("hours_practice"),
                        hours_total=c.get("hours_total"),
                        course_type=c.get("course_type"),
                        description=c.get("description"),
                    )
                    session.add(course)
                    session.flush()
                course_map[c["code"]] = course
                # Also index by name for the major-course mappings
                course_map[c["name"]] = course

        # 5. 导入专业-课程关联
        print("[5/6] 导入专业-课程关联...")
        count_mc = 0
        for uni_key in uni_map:
            mc_data = load_json(f"{uni_key}_major_courses.json")
            for mc in mc_data:
                major_key = f"{uni_key}:{mc['major']}"
                major = major_map.get(major_key)
                if not major:
                    print(f"  警告：找不到专业 {major_key}")
                    continue
                course = course_map.get(mc["course"])
                if not course:
                    print(f"  警告：找不到课程 {mc['course']}")
                    continue

                existing = session.query(MajorCourse).filter_by(
                    major_id=major.id, course_id=course.id
                ).first()
                if not existing:
                    major_course = MajorCourse(
                        major_id=major.id,
                        course_id=course.id,
                        is_required=mc.get("is_required", True),
                        semester=mc.get("semester"),
                        category=mc.get("category"),
                    )
                    session.add(major_course)
                    count_mc += 1
        print(f"  共导入 {count_mc} 条专业-课程关联")

        # 6. 为每个专业创建培养方案
        print("[6/6] 创建培养方案...")
        count_plans = 0
        for major_key, major in major_map.items():
            existing = session.query(CultivationPlan).filter_by(
                major_id=major.id, year=2024
            ).first()
            if not existing:
                plan = CultivationPlan(
                    major_id=major.id,
                    year=2024,
                    total_credits=major.total_credits,
                    description=f"{major.name} 2024级培养方案",
                )
                session.add(plan)
                session.flush()
                count_plans += 1

                # 创建课程组
                groups = [
                    ("通识基础课", 40, True),
                    ("学科基础课", 30, True),
                    ("专业方向课", 25, False),
                    ("实践教学环节", 14, True),
                ]
                for gname, gcredits, gcompulsory in groups:
                    group = PlanCourseGroup(
                        plan_id=plan.id,
                        group_name=gname,
                        required_credits=gcredits,
                        is_compulsory=gcompulsory,
                    )
                    session.add(group)

        session.commit()
        print(f"  共创建 {count_plans} 个培养方案")

        # 统计
        unis = session.query(University).count()
        schools = session.query(School).count()
        majors = session.query(Major).count()
        courses = session.query(Course).count()
        mc = session.query(MajorCourse).count()
        plans = session.query(CultivationPlan).count()
        groups = session.query(PlanCourseGroup).count()

        print("\n=== 数据导入完成 ===")
        print(f"大学: {unis} | 学院: {schools} | 专业: {majors}")
        print(f"课程: {courses} | 专业-课程关联: {mc}")
        print(f"培养方案: {plans} | 课程组: {groups}")

    except Exception as e:
        session.rollback()
        print(f"错误: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_all()
