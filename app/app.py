from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # 세션 미들웨어 추가
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
from dotenv import load_dotenv
load_dotenv()  # .env 파일에서 환경 변수를 로드

# 세션 미들웨어 추가
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-this",  # 실제 프로젝트에서는 보안 키 변경 필요
    max_age=1800  # 세션 만료 시간 (초)
)

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

# 결과 페이지 핸들러 - GET 방식
from gtts import gTTS

@app.get("/result")
async def result_page(request: Request):
    result_data = request.session.get("analysis_result", {})

    # TTS 파일 생성
    text = result_data.get("friendly_message", "")
    if text:
        tts = gTTS(text=text, lang='ko')
        audio_path = ROOT_PATH / "static" / "audio" / "result.mp3"
        audio_path.parent.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 생성
        tts.save(str(audio_path))
    
    if "analysis_result" in request.session:
        del request.session["analysis_result"]

    return templates.TemplateResponse("result.html", {
        "request": request,
        "animal": result_data.get("animal", ""),
        "info": text,
        "img_path": result_data.get("img_path", ""),
        "audio_file": "/static/audio/result.mp3"  # 오디오 경로 전달
    })
