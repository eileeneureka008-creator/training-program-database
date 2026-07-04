-- 培养方案数据库 DDL
-- SQLite 版本

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS university (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    short_name TEXT
);

CREATE TABLE IF NOT EXISTS school (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    university_id INTEGER NOT NULL,
    FOREIGN KEY (university_id) REFERENCES university(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS major (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT,
    school_id INTEGER NOT NULL,
    degree_type TEXT DEFAULT '学士',
    duration TEXT DEFAULT '4年',
    total_credits REAL CHECK(total_credits >= 0),
    FOREIGN KEY (school_id) REFERENCES school(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    name_en TEXT,
    credits REAL CHECK(credits >= 0),
    hours_theory INTEGER CHECK(hours_theory >= 0),
    hours_practice INTEGER CHECK(hours_practice >= 0),
    hours_total INTEGER CHECK(hours_total >= 0),
    course_type TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS major_course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    is_required BOOLEAN DEFAULT 1,
    semester INTEGER,
    category TEXT,
    FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    UNIQUE(major_id, course_id)
);

CREATE TABLE IF NOT EXISTS cultivation_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    major_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_credits REAL CHECK(total_credits >= 0),
    description TEXT,
    FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plan_course_group (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    required_credits REAL,
    is_compulsory BOOLEAN DEFAULT 1,
    FOREIGN KEY (plan_id) REFERENCES cultivation_plan(id) ON DELETE CASCADE
);
