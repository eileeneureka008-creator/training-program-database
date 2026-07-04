"""自然语言查询 → SQL 转换引擎

基于规则匹配，支持中文自然语言查询转换为 SQL 查询。
识别关键词 → 意图分类 → 模板填充 → SQL 生成 → 执行返回结果
"""
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import (
    University, School, Major, Course, MajorCourse, CultivationPlan
)


class NL2SQLEngine:
    def __init__(self, session: Session):
        self.session = session
        self._build_knowledge()

    def _build_knowledge(self):
        """构建已知实体（专业名、学院名、课程名、大学名）"""
        self.major_names = {m.name for m in self.session.query(Major).all()}
        self.school_names = {s.name for s in self.session.query(School).all()}
        self.course_names = {c.name for c in self.session.query(Course).all()}
        self.uni_names = {u.name for u in self.session.query(University).all()}
        self.uni_shorts = {u.short_name for u in self.session.query(University).all()}

    def _find_entity(self, text: str, entities: set) -> str:
        """在文本中查找匹配的实体"""
        for entity in sorted(entities, key=lambda x: -len(x)):
            if entity in text:
                return entity
        return None

    def _classify_intent(self, text: str) -> str:
        """意图分类"""
        patterns = [
            ("compare_required_courses", r"(比较|对比).*(必修课|课程)"),
            ("compare_credits", r"(比较|对比).*(学分|总学分)"),
            ("compare_courses", r"(比较|对比).*(课程)"),
            ("required_courses", r"(必修课|必修为)"),
            ("total_credits", r"(总学分|学分要求)"),
            ("course_info", r"(学分|学时|课程信息).*(多少|是多少|查询)"),
            ("majors_by_course", r"(哪些专业|什么专业|哪个专业).*(有|开设|包含)"),
            ("school_overview", r"(学院.*专业|学院.*培养)"),
            ("search_courses", r"(搜索|查找|找|有没有).*课程"),
            ("list_majors", r"(有哪些专业|所有专业|专业列表)"),
            ("list_schools", r"(有哪些学院|所有学院|学院列表)"),
            ("compare_all", r"(完全对比|全面对比|对比分析)"),
        ]
        for intent, pattern in patterns:
            if re.search(pattern, text):
                return intent
        return "unknown"

    def execute(self, text: str) -> dict:
        """执行自然语言查询"""
        intent = self._classify_intent(text)
        major_name = self._find_entity(text, self.major_names)
        course_name = self._find_entity(text, self.course_names)
        school_name = self._find_entity(text, self.school_names)
        uni_name = self._find_entity(text, self.uni_names)

        handler = getattr(self, f"_handle_{intent}", self._handle_unknown)
        result = handler(text, major_name, course_name, school_name, uni_name)
        result["intent"] = intent
        return result

    def _handle_required_courses(self, text, major_name, course_name, school_name, uni_name):
        if not major_name:
            return {"error": "未能识别专业名称，请明确指定专业", "hint": "如：金融学有哪些必修课"}
        majors = self.session.query(Major).filter_by(name=major_name).all()
        if not majors:
            return {"error": f"未找到专业: {major_name}"}
        results = []
        for m in majors:
            courses = (
                self.session.query(Course.name, Course.credits, Course.hours_total, MajorCourse.semester)
                .join(MajorCourse, Course.id == MajorCourse.course_id)
                .filter(MajorCourse.major_id == m.id, MajorCourse.is_required == True)
                .order_by(MajorCourse.semester)
                .all()
            )
            school = self.session.query(School).filter_by(id=m.school_id).first()
            uni = self.session.query(University).filter_by(id=school.university_id).first() if school else None
            results.append({
                "major": m.name,
                "university": uni.name if uni else "",
                "courses": [{"name": c.name, "credits": c.credits, "hours": c.hours_total, "semester": c.semester} for c in courses],
                "count": len(courses),
            })
        return {"results": results}

    def _handle_course_info(self, text, major_name, course_name, school_name, uni_name):
        if not course_name:
            return {"error": "未能识别课程名称，请明确指定课程", "hint": "如：高等数学的学分是多少"}
        courses = self.session.query(Course).filter(Course.name.like(f"%{course_name}%")).all()
        if not courses:
            return {"error": f"未找到课程: {course_name}"}
        return {"results": [
            {"name": c.name, "code": c.code, "credits": c.credits,
             "hours_theory": c.hours_theory, "hours_practice": c.hours_practice,
             "hours_total": c.hours_total, "course_type": c.course_type,
             "description": c.description}
            for c in courses
        ]}

    def _handle_total_credits(self, text, major_name, course_name, school_name, uni_name):
        if not major_name:
            return {"error": "未能识别专业名称", "hint": "如：金融学的总学分是多少"}
        majors = self.session.query(Major).filter_by(name=major_name).all()
        if not majors:
            return {"error": f"未找到专业: {major_name}"}
        results = []
        for m in majors:
            school = self.session.query(School).filter_by(id=m.school_id).first()
            uni = self.session.query(University).filter_by(id=school.university_id).first() if school else None
            results.append({
                "major": m.name,
                "university": uni.name if uni else "",
                "total_credits": m.total_credits,
                "degree_type": m.degree_type,
                "duration": m.duration,
            })
        return {"results": results}

    def _handle_majors_by_course(self, text, major_name, course_name, school_name, uni_name):
        if not course_name:
            return {"error": "未能识别课程名称", "hint": "如：哪些专业有高等数学"}
        courses = self.session.query(Course).filter(Course.name.like(f"%{course_name}%")).all()
        if not courses:
            return {"error": f"未找到课程: {course_name}"}
        results = []
        for c in courses:
            majors = (
                self.session.query(Major.name, School.name, University.name, MajorCourse.is_required)
                .join(MajorCourse, Major.id == MajorCourse.major_id)
                .join(School, Major.school_id == School.id)
                .join(University, School.university_id == University.id)
                .filter(MajorCourse.course_id == c.id)
                .all()
            )
            results.append({
                "course": c.name,
                "majors": [{"major": m, "school": s, "university": u, "is_required": r} for m, s, u, r in majors]
            })
        return {"results": results}

    def _handle_school_overview(self, text, major_name, course_name, school_name, uni_name):
        if not school_name:
            return {"error": "未能识别学院名称", "hint": "如：金融学院有哪些专业"}
        schools = self.session.query(School).filter_by(name=school_name).all()
        if not schools:
            return {"error": f"未找到学院: {school_name}"}
        results = []
        for s in schools:
            uni = self.session.query(University).filter_by(id=s.university_id).first()
            majors = self.session.query(Major).filter_by(school_id=s.id).all()
            results.append({
                "school": s.name,
                "university": uni.name if uni else "",
                "majors": [{"name": m.name, "code": m.code, "total_credits": m.total_credits} for m in majors],
                "major_count": len(majors),
            })
        return {"results": results}

    def _handle_search_courses(self, text, major_name, course_name, school_name, uni_name):
        # 提取搜索关键词
        keyword_match = re.search(r"(搜索|查找|找|有没有)(.*?)(课程|课)", text)
        if keyword_match:
            keyword = keyword_match.group(2).strip()
        else:
            keyword = course_name or ""
        if not keyword:
            return {"error": "请提供搜索关键词", "hint": "如：搜索金融课程"}
        courses = self.session.query(Course).filter(
            (Course.name.like(f"%{keyword}%")) | (Course.name_en.like(f"%{keyword}%"))
        ).all()
        return {"results": [
            {"name": c.name, "code": c.code, "credits": c.credits, "course_type": c.course_type}
            for c in courses
        ]}

    def _handle_list_majors(self, text, major_name, course_name, school_name, uni_name):
        query = self.session.query(Major, School, University).join(School, Major.school_id == School.id).join(University, School.university_id == University.id)
        if uni_name:
            query = query.filter(University.name == uni_name)
        if school_name:
            query = query.filter(School.name == school_name)
        results = query.all()
        return {"results": [
            {"name": m.name, "code": m.code, "school": s.name, "university": u.name, "total_credits": m.total_credits}
            for m, s, u in results
        ]}

    def _handle_list_schools(self, text, major_name, course_name, school_name, uni_name):
        query = self.session.query(School, University).join(University, School.university_id == University.id)
        if uni_name:
            query = query.filter(University.name == uni_name)
        results = query.all()
        return {"results": [
            {"name": s.name, "university": u.name} for s, u in results
        ]}

    def _handle_compare_required_courses(self, text, major_name, course_name, school_name, uni_name):
        from src.queries.cross_compare import compare_major_courses
        if not major_name:
            return {"error": "请指定要对比的专业", "hint": "如：对比金融学的课程"}
        result = compare_major_courses(self.session, major_name)
        return {"results": result}

    def _handle_compare_credits(self, text, major_name, course_name, school_name, uni_name):
        from src.queries.cross_compare import compare_credits
        if not major_name:
            return {"error": "请指定要对比的专业", "hint": "如：对比金融学的学分"}
        result = compare_credits(self.session, major_name)
        return {"results": result}

    def _handle_compare_courses(self, text, major_name, course_name, school_name, uni_name):
        from src.queries.cross_compare import list_common_courses
        if not major_name:
            return {"error": "请指定要对比的专业", "hint": "如：对比经济学课程"}
        result = list_common_courses(self.session, major_name)
        return {"results": result}

    def _handle_compare_all(self, text, major_name, course_name, school_name, uni_name):
        from src.queries.cross_compare import compare_major_courses, compare_credits, compare_course_structure
        if not major_name:
            return {"error": "请指定要对比的专业", "hint": "如：全面对比金融学"}
        return {"results": {
            "courses": compare_major_courses(self.session, major_name),
            "credits": compare_credits(self.session, major_name),
            "structure": compare_course_structure(self.session, major_name),
        }}

    def _handle_unknown(self, text, major_name, course_name, school_name, uni_name):
        return {
            "error": "未能理解您的查询意图",
            "hint": "支持的查询类型：查必修课、查学分、查课程信息、查专业列表、学院概览、搜索课程、跨校对比",
            "recognized_entities": {
                "major": major_name,
                "course": course_name,
                "school": school_name,
                "university": uni_name,
            },
        }
