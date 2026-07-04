# 培养方案数据库系统

西南财经大学 & 上海财经大学培养方案查询与跨校对比系统。

## 功能

### 子模块 A：培养方案数据库
- 数据预处理与结构化存储
- 关系型数据库设计（SQLite + SQLAlchemy ORM）
- 支持 6 项核心查询：
  1. 查询某专业的必修课列表
  2. 查询某门课程的学分、学时信息
  3. 查询某专业的总学分要求
  4. 查询开设某门课程的所有专业
  5. 查询某学院下所有专业的培养方案概览
  6. 关键词模糊搜索课程名称

### 子模块 B：跨校培养方案对比分析
- 整合两所财经大学数据
- 跨校对比查询（课程异同、学分对比、课程结构、共同课程）
- 自然语言查询接口（中文 → SQL 自动转换）

### 用户界面
- Web 界面（FastAPI + Jinja2）
- CLI 命令行界面
- OpenAPI/Swagger 自动文档

## 快速开始

### 环境要求
- Python 3.10+

### 安装

    pip install -r requirements.txt

### 导入数据

    python -m src.database.seed

### 启动 Web 服务

    uvicorn src.web.main:app --reload

访问：
- Web UI: http://localhost:8000
- API 文档: http://localhost:8000/docs

### CLI 使用

    python src/cli.py

命令示例：

    查询> required 金融学          # 查询必修课
    查询> course 高等数学           # 查询课程信息
    查询> search 金融               # 模糊搜索
    查询> school 金融学院           # 学院概览
    查询> compare 金融学            # 跨校对比
    查询> ask 经济学有哪些必修课     # 自然语言查询

### 运行测试

    pytest tests/ -v

## 项目结构

    ├── data/sample/               # 样本数据（JSON）
    ├── src/
    │   ├── config.py              # 配置
    │   ├── database/              # 数据库模型 & 数据导入
    │   ├── queries/               # 查询模块（基础+跨校对比）
    │   ├── nl2sql/                # 自然语言→SQL引擎
    │   ├── web/                   # FastAPI Web应用
    │   └── cli.py                 # CLI界面
    ├── tests/                     # 测试用例
    └── requirements.txt

## 数据范围

- **西南财经大学**：金融学院、会计学院、经济学院、统计学院（9个专业）
- **上海财经大学**：金融学院、会计学院、经济学院（7个专业）
- 数据库共含 125 门课程，532 条专业-课程关联

## 技术栈

- 数据库：SQLite + SQLAlchemy ORM
- 后端：FastAPI
- 前端：Jinja2 模板 + 原生 JS
- 数据处理：pandas, BeautifulSoup
