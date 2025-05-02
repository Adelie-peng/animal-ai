from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.routers import analyze, predict, upload

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
app = FastAPI(
    title="ZooBuddy API",
    description="동물 이미지 분석 및 정보 제공 API",
    version="1.0.0"
)

# 세션 미들웨어 추가
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-this"),
    max_age=1800  # 세션 만료 시간 (초)
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=str(ROOT_PATH / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT_PATH / "app" / "templates"))

# Gemini AI를 사용하여 동물 소개 문구 생성
def generate_animal_greeting(animal_class):
    try:
        if not GEMINI_API_KEY:
            return f"{animal_class.replace('a ', '')} 사진이네요!"
            
        # Gemini 모델 인스턴스 생성
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 프롬프트 작성
        prompt = f"""
        다음 동물 종류에 대해 사진을 본 것처럼 자연스러운 한국어 인사말을 작성해주세요.
        동물: {animal_class}
        
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
        return f"{animal_class.replace('a ', '')} 사진이네요!"

# 루트 경로 핸들러
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 결과 페이지 핸들러 - GET 방식
@app.get("/result")
async def result_page(request: Request):
    # 세션에서 분석 결과 데이터 가져오기
    result_data = request.session.get("analysis_result", {})
    
    # 동물 클래스 가져오기
    animal = result_data.get("animal", "")
    
    # Gemini AI로 동물 소개 문구 생성
    animal_greeting = ""
    if animal:
        animal_greeting = generate_animal_greeting(animal)
        # 세션에 저장 (템플릿에서 사용)
        result_data["animal_greeting"] = animal_greeting
    
    # 선택적으로 세션에서 데이터 삭제 (일회성 데이터로 처리)
    if "analysis_result" in request.session:
        del request.session["analysis_result"]
    
    return templates.TemplateResponse("result.html", {
        "request": request,
        "animal": result_data.get("animal", ""),
        "animal_greeting": animal_greeting,
        "info": result_data.get("friendly_message", ""),
        "img_path": result_data.get("img_path", "")
    })

# 분석 API - 기존 라우터 오버라이드
@app.post("/api/analyze/")
async def analyze_animal(request: Request, file: UploadFile = File(...)):
    """
    동물 이미지를 분석하여 종류를 식별하고 관련 정보를 반환합니다.
    
    Args:
        request (Request): FastAPI 요청 객체 (세션 접근용)
        file (UploadFile): 분석할 동물 이미지 파일
    
    Returns:
        JSONResponse: 분석 결과를 포함하는 응답 객체
    """
    try:
        # 이미지 파일 검증
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        
        # 이미지 데이터 읽기
        contents = await file.read()
        
        # 이미지 크기 확인
        from PIL import Image
        import io
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            if image.size[0] < 64 or image.size[1] < 64:
                raise HTTPException(status_code=400, detail="Image too small")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
            
        # 이미지 분석
        try:
            # 세그멘테이션 및 분류 수행
            from app.services.sam_service import sam_service
            from app.services.classifier_service import AnimalClassifier
            from app.services.db_service import AnimalDatabase 
            from app.services.chat_service import ChatBotService
            
            # 서비스 인스턴스
            classifier = AnimalClassifier()
            db_service = AnimalDatabase()
            chatbot_service = ChatBotService()
            
            # 중앙점 계산 (기본 포인트 대신)
            input_point = (image.size[0] // 2, image.size[1] // 2)
            
            # 세그멘테이션 수행
            _, mask, _ = sam_service.segment(
                image_path=io.BytesIO(contents), 
                input_point=input_point
            )
            
            # 동물 분류
            classification_result = classifier.classify_animal(image, mask)
            
            # 신뢰도 점수 확인
            confidence = classification_result.get("confidence", 0)
            
            # 신뢰도가 낮으면 오류 반환
            if confidence < 0.4:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "animal": None,
                        "confidence": confidence,
                        "message": "동물을 정확히 인식하지 못했습니다."
                    }
                )
            
            # 데이터베이스에서 정보 조회
            animal_info = db_service.get_info(classification_result["class"])
            if not animal_info:
                animal_info = {"message": "Additional information not available"}
            
            # 챗봇 응답 생성
            friendly_message = chatbot_service.generate_response(
                classification_result["class"], 
                animal_info
            )
            
            # 결과 생성
            result = {
                "success": True,
                "animal": classification_result["class"],
                "confidence": classification_result["confidence"],
                "top3_predictions": classification_result["top3"],
                "info": animal_info,
                "friendly_message": friendly_message
            }
            
            # 세션에 분석 결과 저장
            request.session["analysis_result"] = {
                "animal": classification_result["class"],
                "confidence": classification_result["confidence"],
                "friendly_message": friendly_message,
                "img_path": ""  # 이미지 경로가 필요하면 여기에 추가
            }
            
            return JSONResponse(content=result)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
            
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "error": e.detail}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Unexpected error: {str(e)}"}
        )
        
    finally:
        # 파일 핸들러 정리
        await file.close()

# 분석 결과 API
@app.post("/api/analyze/result")
async def get_analysis_result(request: Request):
    """
    세션에 저장된 분석 결과를 JSON 형식으로 반환하는 API
    
    Returns:
        JSONResponse: 분석 결과
    """
    try:
        # 세션에서 분석 결과 데이터 가져오기
        result_data = request.session.get("analysis_result", {})
        
        if not result_data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "분석 결과를 찾을 수 없습니다"}
            )
        
        # 동물 클래스 가져오기
        animal = result_data.get("animal", "")
        
        # Gemini AI로 동물 소개 문구 생성
        animal_greeting = ""
        if animal:
            animal_greeting = generate_animal_greeting(animal)
        
        return {
            "success": True,
            "animal": result_data.get("animal", ""),
            "animal_greeting": animal_greeting,
            "friendly_message": result_data.get("friendly_message", ""),
            "img_path": result_data.get("img_path", ""),
            "confidence": result_data.get("confidence", 0)
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# 이미지 업로드 API
@app.post("/api/upload/")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """
    이미지 업로드 및 임시 저장
    
    Args:
        request (Request): FastAPI 요청 객체
        file (UploadFile): 업로드할 파일
    
    Returns:
        JSONResponse: 업로드 결과
    """
    try:
        # 파일 타입 검증
        if not file.content_type.startswith("image/"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "이미지 파일만 업로드 가능합니다."}
            )
        
        # 이미지 데이터 읽기
        contents = await file.read()
        
        # 임시 파일 경로
        temp_dir = ROOT_PATH / "static" / "uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 파일 저장
        file_path = temp_dir / f"{file.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 상대 경로 (static 기준)
        relative_path = f"/static/uploads/{file.filename}"
        
        # 세션에 경로 저장
        if "analysis_result" in request.session:
            request.session["analysis_result"]["img_path"] = relative_path
        else:
            request.session["analysis_result"] = {"img_path": relative_path}
        
        return JSONResponse(
            content={
                "success": True,
                "filename": file.filename,
                "path": relative_path
            }
        )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
        
    finally:
        await file.close()

# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)}
    )

# 라우터 등록 - 기본 라우터는 유지 (app.py에서 오버라이드한 엔드포인트 제외)
app.include_router(predict.router, prefix="/api")
app.include_router(upload.router, prefix="/api", tags=["upload"])
