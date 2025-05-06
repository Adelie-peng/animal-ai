from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Tuple, Optional
from app.services.sam_service import sam_service
from app.services.classifier_service import AnimalClassifier
from app.services.db_service import AnimalDatabase
from app.services.chat_service import ChatBotService
from app.services.animal_data import animal_data_service
from app.services.storage_service import TempStorageService
from PIL import Image
import numpy as np
import io
import logging
import uuid

# 로거 설정
logger = logging.getLogger(__name__)

# 응답 모델 정의
class AnimalPrediction(BaseModel):
    animal: str
    confidence: float

class AnalysisResponse(BaseModel):
    animal: str
    confidence: float
    top3_predictions: List[Tuple[str, float]]
    info: dict
    friendly_message: str

router = APIRouter()

# 서비스 인스턴스
classifier = AnimalClassifier()
db_service = AnimalDatabase()
chatbot_service = ChatBotService()
temp_storage = TempStorageService()  # 싱글톤 인스턴스 사용

@router.post("/analyze/")
async def analyze_animal(request: Request, file: UploadFile = File(...)):
    """
    동물 이미지를 분석하여 종류를 식별하고 관련 정보를 반환합니다.
    
    Args:
        request (Request): FastAPI 요청 객체 (세션 접근용)
        file (UploadFile): 분석할 동물 이미지 파일
    
    Returns:
        RedirectResponse: 결과 페이지로 리다이렉트
    
    Raises:
        HTTPException: 이미지 처리 또는 분석 중 오류 발생 시
    """
    try:
        # 이미지 파일 검증
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        
        # 이미지 로드
        image_data = await file.read()
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to process image")

        # 이미지 크기 검증
        if image.size[0] < 64 or image.size[1] < 64:
            raise HTTPException(status_code=400, detail="Image too small")

        # 중앙점 계산 (기본 포인트 대신)
        input_point = (image.size[0] // 2, image.size[1] // 2)
        
        try:
            # 세그멘테이션 수행
            _, mask, _ = sam_service.segment(
                image_path=file.file, 
                input_point=input_point
            )
            
            # 동물 분류
            classification_result = classifier.classify_animal(image, mask)
            
            # 분류 결과 로깅 (디버깅용)
            logger.info(f"CLIP 분류 결과: {classification_result['class']}")
            logger.info(f"상위 3개 결과: {classification_result['top3']}")
            
            # 데이터베이스에서 정보 조회
            animal_info = db_service.get_info(classification_result["class"])
            if not animal_info:
                logger.warning(f"No information found for {classification_result['class']}")
                animal_info = {"message": "Additional information not available"}
            
            # 챗봇 응답 생성
            friendly_message = chatbot_service.generate_response(
                classification_result["class"], 
                animal_info
            )
            
            # 번역된 동물 이름을 가져오기
            cleaned_animal_name = classification_result["class"].replace("a ", "").strip()
            korean_name = animal_data_service.translate_animal_name(
                cleaned_animal_name, 
                'en', 
                'ko'
            )

            # UUID 생성 및 임시 저장소에 분석 결과 저장
            result_id = str(uuid.uuid4())
            temp_storage.store(result_id, {
                "animal": classification_result["class"],
                "animal_greeting": f"{korean_name or cleaned_animal_name} 사진이네요!",
                "friendly_message": friendly_message,
                "img_path": ""
            })
            
            # 주기적으로 만료된 임시 데이터 정리
            temp_storage.cleanup()
            
            # 결과 페이지로 리다이렉트
            return RedirectResponse(f"/result?id={result_id}", status_code=303)

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to analyze image")

    finally:
        # 파일 핸들러 정리
        await file.close()

# 결과 조회 엔드포인트
@router.get("/results/{result_id}")
async def get_analysis_results(result_id: str):
    """
    임시 저장소에서 분석 결과를 가져옵니다.
    
    Args:
        result_id (str): 분석 결과 ID
        
    Returns:
        JSONResponse: 분석 결과를 포함하는 응답
    """
    # 임시 저장소에서 결과 조회
    result = temp_storage.get(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found or expired")
    
    return JSONResponse(content=result)
