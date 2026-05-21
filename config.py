"""
配置文件
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Railway 提供 PostgreSQL，本地开发用 SQLite
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR}/ecommerce.db}"
)

# JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "railway-prod-secret-2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# 上传
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
