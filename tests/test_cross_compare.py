"""跨校对比查询测试 — 至少 5 个测试用例"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DATABASE_URL
from src.database.models import get_session, Base
from src.queries.cross_compare import (
    compare_major_courses, compare_credits, compare_course_structure, list_common_courses
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class TestCrossCompare:
    """跨校对比测试 — 5 个查询用例"""

    def test_compare_finance_courses(self, session):
        """测试用例1：对比金融学在两校的课程设置异同"""
        result = compare_major_courses(session, "金融学")
        assert "error" not in result
        assert result["major_name"] == "金融学"
        assert "common_courses" in result
        assert "only_swufe" in result
        assert "only_sufe" in result
        assert result["common_count"] > 0  # 应该有共同课程

    def test_compare_accounting_credits(self, session):
        """测试用例2：对比会计学在两校的总学分要求"""
        result = compare_credits(session, "会计学")
        assert "comparisons" in result
        assert len(result["comparisons"]) == 2
        for comp in result["comparisons"]:
            assert "total_credits" in comp or "error" in comp

    def test_compare_economics_structure(self, session):
        """测试用例3：对比经济学的课程结构"""
        result = compare_course_structure(session, "经济学")
        assert "swufe" in result
        assert "sufe" in result

    def test_common_finance_courses(self, session):
        """测试用例4：列出金融学在两校的共同课程"""
        result = list_common_courses(session, "金融学")
        assert "common_courses" in result
        assert result["common_count"] > 0

    def test_compare_all_finance_engineering(self, session):
        """测试用例5：对比金融工程的全方位信息"""
        courses_result = compare_major_courses(session, "金融工程")
        credits_result = compare_credits(session, "金融工程")
        structure_result = compare_course_structure(session, "金融工程")

        assert "error" not in courses_result
        assert "error" not in credits_result
        assert structure_result is not None

        # 验证有学分差异信息
        assert "comparisons" in credits_result
        assert len(credits_result["comparisons"]) == 2
