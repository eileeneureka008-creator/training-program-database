"""数据库与应用配置"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'data', 'cultivation.db')}"
)

SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "data", "sample")

# 支持的大学
UNIVERSITIES = {
    "swufe": "西南财经大学",
    "sufe": "上海财经大学",
}
