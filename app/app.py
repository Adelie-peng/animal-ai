from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware  # 세션 미들웨어 추가
from pathlib import Path
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.routers import analyze, predict, upload
from app.services.animal_data import animal_data_service

# 환경 변수 로드
load_dotenv()

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 프로젝트 루트 경로 설정
ROOT_PATH = Path(__file__).parent.parent

# MobileSAM 경로 설정 및 시스템 경로에 추가
MOBILE_SAM_PATH = ROOT_PATH / 'external' / 'MobileSAM'
sys.path.append(str(MOBILE_SAM_PATH))

# FastAPI 앱 초기화
app = FastAPI()

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

# 과(Family) 수준의 기본 번역 매핑
FAMILY_TRANSLATIONS = {
    "deer": "사슴",
    "dog": "개",
    "cat": "고양이",
    "lion": "사자",
    "tiger": "호랑이",
    "bear": "곰",
    "horse": "말",
    "panda": "판다",
    "fox": "여우",
    "rabbit": "토끼",
    "wolf": "늑대",
    "monkey": "원숭이",
    "elephant": "코끼리",
    "giraffe": "기린",
    "zebra": "얼룩말"
}

# 동물 이름 전처리 함수
def preprocess_animal_name(animal_class):
    """CLIP에서 반환되는 동물 이름을 전처리하는 함수"""
    # "a dog", "the cat" 등에서 관사 제거
    cleaned_name = animal_class.lower().replace('a ', '').replace('the ', '').strip()
    return cleaned_name

# Gemini AI를 사용하여 동물 소개 문구 생성
def generate_animal_greeting(animal_class):
    try:
        if not GEMINI_API_KEY:
            return f"{animal_class.replace('a ', '')} 사진이네요!"
            
        # 동물 이름 전처리
        cleaned_name = preprocess_animal_name(animal_class)
        
        # 영어명을 한글명으로 번역 시도
        korean_name = animal_data_service.translate_animal_name(cleaned_name, 'en', 'ko')
        
        # 번역이 안 된 경우 과(Family) 수준의 매핑 사용
        if not korean_name:
            korean_name = FAMILY_TRANSLATIONS.get(cleaned_name, cleaned_name)
            
        # Gemini 모델 인스턴스 생성
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 프롬프트 작성
        prompt = f"""
        다음 동물 종류에 대해 사진을 본 것처럼 자연스러운 한국어 인사말을 작성해주세요.
        동물: {korean_name}
        
        예시:
        - 귀여운 고양이 사진이네요!
        - 멋진 호랑이가 있군요!
        - 아름다운 앵무새를 찍으셨네요!
        
        한 문장으로 짧게 작성해주세요. 끝에 느낌표나 물음표, 물결 표시를 붙여 생동감을 주고, 동물 종류를 한국어로 표현해주세요.
        """
        
        # 응답 생성
        response = model.generate_content(prompt)
        greeting = response.text.strip()
        
        # 응답이 너무 길면 적절히 자르기
        if len(greeting) > 30:
            greeting = greeting[:30] + "!"
            
        return greeting
    except Exception as e:
        print(f"Gemini API 호출 오류: {str(e)}")
        # Gemini 호출에 실패한 경우에도 한글 이름 사용
        cleaned_name = preprocess_animal_name(animal_class)
        korean_name = animal_data_service.translate_animal_name(cleaned_name, 'en', 'ko')
        if not korean_name:
            korean_name = FAMILY_TRANSLATIONS.get(cleaned_name, cleaned_name)
        return f"{korean_name} 사진이네요!"

# 루트 경로 핸들러
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 결과 페이지 핸들러 - GET 방식
@app.get("/result")
async def result_page(request: Request):
    # 세션에서 분석 결과 데이터 가져오기
    result_data = request.session.get("analysis_result", {})
    
    # 디버깅: 세션 데이터 출력
    print(f"DEBUG: Session result_data: {result_data}")
    
    # 동물 클래스 가져오기
    animal = result_data.get("animal", "")
    
    # Gemini AI로 동물 소개 문구 생성
    animal_greeting = ""
    if animal:
        animal_greeting = generate_animal_greeting(animal)
        print(f"DEBUG: Generated greeting: {animal_greeting}")
        # 세션에 저장 (템플릿에서 사용)
        result_data["animal_greeting"] = animal_greeting
    
    # 디버깅: 최종 템플릿 데이터 출력
    template_data = {
        "request": request,
        "animal": result_data.get("animal", ""),
        "animal_greeting": animal_greeting,
        "info": result_data.get("friendly_message", ""),
        "img_path": result_data.get("img_path", "")
    }
    print(f"DEBUG: Template data: {template_data}")
    
    # 선택적으로 세션에서 데이터 삭제 (일회성 데이터로 처리)
    if "analysis_result" in request.session:
        del request.session["analysis_result"]
    
    return templates.TemplateResponse("result.html", template_data)
