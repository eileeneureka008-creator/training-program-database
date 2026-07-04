"""SQLAlchemy ORM 模型定义"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, ForeignKey,
    UniqueConstraint, CheckConstraint, create_engine, event
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.engine import Engine

Base = declarative_base()


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """启用 SQLite 外键约束"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class University(Base):
    __tablename__ = "university"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    short_name = Column(String(20))

    schools = relationship("School", back_populates="university", cascade="all, delete-orphan")


class School(Base):
    __tablename__ = "school"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    university_id = Column(Integer, ForeignKey("university.id", ondelete="CASCADE"), nullable=False)

    university = relationship("University", back_populates="schools")
    majors = relationship("Major", back_populates="school", cascade="all, delete-orphan")


class Major(Base):
    __tablename__ = "major"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20))
    school_id = Column(Integer, ForeignKey("school.id", ondelete="CASCADE"), nullable=False)
    degree_type = Column(String(20), default="学士")
    duration = Column(String(10), default="4年")
    total_credits = Column(Float)

    __table_args__ = (
        CheckConstraint("total_credits >= 0", name="ck_major_credits"),
    )

    school = relationship("School", back_populates="majors")
    major_courses = relationship("MajorCourse", back_populates="major", cascade="all, delete-orphan")
    cultivation_plans = relationship("CultivationPlan", back_populates="major", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200))
    credits = Column(Float)
    hours_theory = Column(Integer)
    hours_practice = Column(Integer)
    hours_total = Column(Integer)
    course_type = Column(String(20))  # 必修/选修/通识基础等
    description = Column(Text)

    __table_args__ = (
        CheckConstraint("credits >= 0", name="ck_course_credits"),
        CheckConstraint("hours_theory >= 0", name="ck_course_theory_hours"),
        CheckConstraint("hours_practice >= 0", name="ck_course_practice_hours"),
        CheckConstraint("hours_total >= 0", name="ck_course_total_hours"),
    )

    major_courses = relationship("MajorCourse", back_populates="course", cascade="all, delete-orphan")


class MajorCourse(Base):
    __tablename__ = "major_course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    major_id = Column(Integer, ForeignKey("major.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    is_required = Column(Boolean, default=True)
    semester = Column(Integer)
    category = Column(String(50))  # 通识基础/学科基础/专业方向/实践教学

    __table_args__ = (
        UniqueConstraint("major_id", "course_id", name="uq_major_course"),
    )

    major = relationship("Major", back_populates="major_courses")
    course = relationship("Course", back_populates="major_courses")


class CultivationPlan(Base):
    __tablename__ = "cultivation_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    major_id = Column(Integer, ForeignKey("major.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    total_credits = Column(Float)
    description = Column(Text)

    __table_args__ = (
        CheckConstraint("total_credits >= 0", name="ck_plan_credits"),
    )

    major = relationship("Major", back_populates="cultivation_plans")
    course_groups = relationship("PlanCourseGroup", back_populates="plan", cascade="all, delete-orphan")


class PlanCourseGroup(Base):
    __tablename__ = "plan_course_group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("cultivation_plan.id", ondelete="CASCADE"), nullable=False)
    group_name = Column(String(100), nullable=False)
    required_credits = Column(Float)
    is_compulsory = Column(Boolean, default=True)

    plan = relationship("CultivationPlan", back_populates="course_groups")


def get_session(database_url: str):
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
