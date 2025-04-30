from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys

# 프로젝트 루트 경로 설정
ROOT_PATH = Path(__file__).parent.parent

# MobileSAM 경로 설정 및 시스템 경로에 추가
MOBILE_SAM_PATH = ROOT_PATH / 'external' / 'MobileSAM'
sys.path.append(str(MOBILE_SAM_PATH))

# FastAPI 앱 초기화
app = FastAPI()

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# MobileSAM 모델 가중치 경로 설정 (다른 서비스에서 참조 가능)
MOBILE_SAM_WEIGHTS = MOBILE_SAM_PATH / 'weights' / 'mobile_sam.pt'
