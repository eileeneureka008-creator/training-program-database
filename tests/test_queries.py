"""基本查询测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DATABASE_URL
from src.database.models import get_session, Base, Course, Major
from src.queries.basic import (
    get_required_courses, get_course_info, get_total_credits,
    get_majors_by_course, get_school_plans_overview, search_courses,
    get_all_schools, get_all_majors
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class TestBasicQueries:
    """测试 6 个基本查询功能"""

    def test_get_required_courses(self, session):
        """测试查询某专业的必修课列表"""
        major = session.query(Major).first()
        assert major is not None
        courses = get_required_courses(session, major.id)
        assert isinstance(courses, list)
        if courses:
            assert "name" in courses[0]
            assert "credits" in courses[0]

    def test_get_course_info(self, session):
        """测试查询课程信息"""
        course = session.query(Course).first()
        assert course is not None
        info = get_course_info(session, course_id=course.id)
        assert info is not None
        assert info["name"] == course.name
        assert "credits" in info
        assert "hours_total" in info

    def test_get_course_info_by_code(self, session):
        """测试通过编号查询课程信息"""
        course = session.query(Course).first()
        info = get_course_info(session, course_code=course.code)
        assert info is not None
        assert info["code"] == course.code

    def test_get_total_credits(self, session):
        """测试查询某专业总学分"""
        major = session.query(Major).first()
        info = get_total_credits(session, major.id)
        assert info is not None
        assert "total_credits_required" in info
        assert "category_breakdown" in info

    def test_get_majors_by_course(self, session):
        """测试查询开设某门课程的所有专业"""
        course = session.query(Course).first()
        majors = get_majors_by_course(session, course_id=course.id)
        assert isinstance(majors, list)

    def test_get_school_plans_overview(self, session):
        """测试查询学院培养方案概览"""
        schools = get_all_schools(session)
        assert len(schools) > 0
        overview = get_school_plans_overview(session, schools[0]["id"])
        assert overview is not None
        assert "school_name" in overview
        assert "majors" in overview

    def test_search_courses(self, session):
        """测试模糊搜索课程"""
        results = search_courses(session, "经济")
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_courses_no_match(self, session):
        """测试无匹配搜索"""
        results = search_courses(session, "量子物理xyz")
        assert results == []

    def test_get_all_schools(self, session):
        """测试获取所有学院"""
        schools = get_all_schools(session)
        assert len(schools) > 0
        assert "name" in schools[0]
        assert "university_name" in schools[0]

    def test_get_all_majors(self, session):
        """测试获取所有专业"""
        majors = get_all_majors(session)
        assert len(majors) > 0
        assert "name" in majors[0]
