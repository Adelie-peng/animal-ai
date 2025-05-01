# app/config.py
import os
from pathlib import Path
import secrets

# 프로젝트 루트 경로
ROOT_PATH = Path(__file__).parent.parent

# 외부 모듈 경로
MOBILE_SAM_PATH = ROOT_PATH / 'external' / 'MobileSAM'
MOBILE_SAM_WEIGHTS = MOBILE_SAM_PATH / 'weights' / 'mobile_sam.pt'

# 세션 설정
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
SESSION_MAX_AGE = 1800  # 30분

# 서버 설정
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 8000))
RELOAD = os.environ.get("RELOAD", "true").lower() == "true"

# CORS 설정
CORS_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# 데이터베이스 설정
DB_PATH = ROOT_PATH / 'data' / 'database' / 'animal_data.db'
