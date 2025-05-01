from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
from app.routers import analyze, predict, upload

# 프로젝트 루트 경로 설정
ROOT_PATH = Path(__file__).parent.parent

# MobileSAM 경로 설정 및 시스템 경로에 추가
MOBILE_SAM_PATH = ROOT_PATH / 'external' / 'MobileSAM'
sys.path.append(str(MOBILE_SAM_PATH))

# FastAPI 앱 초기화
app = FastAPI()

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 도메인 허용 (실제 환경에서는 프론트엔드 도메인만 지정)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=str(ROOT_PATH / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT_PATH / "app" / "templates"))

# 라우터 등록
app.include_router(analyze.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(upload.router, prefix="/api")

# MobileSAM 모델 가중치 경로 설정 (다른 서비스에서 참조 가능)
MOBILE_SAM_WEIGHTS = MOBILE_SAM_PATH / 'weights' / 'mobile_sam.pt'

# 루트 경로 핸들러
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 결과 페이지 핸들러
@app.get("/result")
async def result(request: Request, animal: str = "", img_path: str = "", info: str = ""):
    return templates.TemplateResponse("result.html", {
        "request": request,
        "animal": animal,
        "img_path": img_path,
        "info": info
    })