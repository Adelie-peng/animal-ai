from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Tuple, Optional
from app.services.sam_service import sam_service
from app.services.classifier_service import AnimalClassifier
from app.services.db_service import AnimalDatabase
from app.services.chat_service import ChatBotService
from PIL import Image
import numpy as np
import io
import logging

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

@router.post("/analyze/", response_model=AnalysisResponse)
async def analyze_animal(request: Request, file: UploadFile = File(...)) -> AnalysisResponse:
    """
    동물 이미지를 분석하여 종류를 식별하고 관련 정보를 반환합니다.
    
    Args:
        request (Request): FastAPI 요청 객체 (세션 접근용)
        file (UploadFile): 분석할 동물 이미지 파일
    
    Returns:
        AnalysisResponse: 분석 결과를 포함하는 응답 객체
    
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

            # 결과 생성
            result = AnalysisResponse(
                animal=classification_result["class"],
                confidence=classification_result["confidence"],
                top3_predictions=classification_result["top3"],
                info=animal_info,
                friendly_message=friendly_message
            )
            
            # 세션에 분석 결과 저장 (POST-Redirect-GET 패턴용)
            request.session["analysis_result"] = {
                "animal": classification_result["class"],
                "friendly_message": friendly_message,
                "img_path": ""  # 이미지 경로가 필요하면 여기에 추가
            }
            
            return result

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to analyze image")

    finally:
        # 파일 핸들러 정리
        await file.close()
        