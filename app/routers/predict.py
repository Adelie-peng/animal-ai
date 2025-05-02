# 업로드 + 예측 처리
# Upload + Predict 샘플

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
from app.services.model import segment_animal
import logging
from PIL import Image
import io

# 로거 설정
logger = logging.getLogger(__name__)

# 응답 모델 정의
class SegmentationResponse(BaseModel):
    segmented_info: Dict[str, Any]
    message: str

router = APIRouter()

@router.post("/predict", response_model=SegmentationResponse)
async def predict_animal(file: UploadFile = File(...)) -> SegmentationResponse:
    """
    업로드된 이미지에서 동물을 segmentation하여 결과를 반환합니다.
    
    Args:
        file (UploadFile): 분석할 동물 이미지 파일
    
    Returns:
        SegmentationResponse: segmentation 결과를 포함하는 응답 객체
    
    Raises:
        HTTPException: 이미지 처리 또는 분석 중 오류 발생 시
    """
    try:
        # 이미지 파일 검증
        if not file.content_type.startswith("image/"):
            logger.error(f"Invalid file type: {file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an image."
            )

        # 이미지 데이터 읽기
        contents = await file.read()

        # 이미지 검증
        try:
            image = Image.open(io.BytesIO(contents))
            if image.size[0] < 64 or image.size[1] < 64:
                raise HTTPException(
                    status_code=400, 
                    detail="Image too small. Minimum size is 64x64 pixels."
                )
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail="Failed to process image. Please check the image file."
            )

        # Segmentation 수행
        try:
            segmented_image_info = segment_animal(contents)
            logger.info("Successfully segmented animal in image")
            
            return SegmentationResponse(
                segmented_info=segmented_image_info,
                message="Segmentation completed successfully"
            )

        except Exception as e:
            logger.error(f"Segmentation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to segment animal in image"
            )

    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

    finally:
        # 파일 핸들러 정리
        await file.close()
