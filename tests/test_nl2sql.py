"""自然语言查询测试 — 至少 10 个测试用例"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DATABASE_URL
from src.database.models import get_session, Base
from src.nl2sql.engine import NL2SQLEngine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(DATABASE_URL)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def nl_engine(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    return NL2SQLEngine(session)


class TestNL2SQL:
    """NL-to-SQL 引擎测试 — 10+ 个自然语言查询用例"""

    def test_intent_required_courses(self, nl_engine):
        """测试：查询必修课"""
        result = nl_engine.execute("金融学有哪些必修课")
        assert result["intent"] == "required_courses"
        assert "results" in result

    def test_intent_course_info(self, nl_engine):
        """测试：查询课程学分"""
        result = nl_engine.execute("高等数学的学分是多少")
        assert result["intent"] in ("course_info", "search_courses")

    def test_intent_total_credits(self, nl_engine):
        """测试：查询总学分"""
        result = nl_engine.execute("金融学的总学分要求")
        assert result["intent"] == "total_credits"

    def test_intent_majors_by_course(self, nl_engine):
        """测试：哪些专业有某课程"""
        result = nl_engine.execute("哪些专业有微观经济学")
        assert result["intent"] == "majors_by_course"

    def test_intent_school_overview(self, nl_engine):
        """测试：查询学院"""
        result = nl_engine.execute("金融学院有哪些专业")
        assert result["intent"] in ("school_overview", "list_majors")

    def test_intent_search(self, nl_engine):
        """测试：搜索课程"""
        result = nl_engine.execute("搜索金融课程")
        assert result["intent"] == "search_courses"

    def test_intent_compare_credits(self, nl_engine):
        """测试：对比学分"""
        result = nl_engine.execute("对比金融学的学分")
        assert result["intent"] == "compare_credits"

    def test_intent_compare_courses(self, nl_engine):
        """测试：对比课程"""
        result = nl_engine.execute("比较会计学的课程")
        assert result["intent"] == "compare_required_courses"

    def test_intent_list_majors(self, nl_engine):
        """测试：列出专业"""
        result = nl_engine.execute("有哪些专业")
        assert result["intent"] == "list_majors"

    def test_intent_list_schools(self, nl_engine):
        """测试：列出学院"""
        result = nl_engine.execute("有哪些学院")
        assert result["intent"] == "list_schools"

    def test_intent_unknown(self, nl_engine):
        """测试：不可理解的查询"""
        result = nl_engine.execute("今天天气怎么样")
        assert result["intent"] == "unknown"
        assert "error" in result

    def test_entity_recognition(self, nl_engine):
        """测试：实体识别"""
        result = nl_engine.execute("会计学的总学分是多少")
        assert result["intent"] == "total_credits"
