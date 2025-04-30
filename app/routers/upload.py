from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.scraper import scrape_animal_info, korean_to_english
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# 응답 모델 정의
class UploadResponse(BaseModel):
    filename: str
    predicted_animal: str
    animal_info: Dict
    file_size: int

class AnimalInfoResponse(BaseModel):
    input: str
    translated: str
    animal_info: Dict

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)) -> UploadResponse:
    """
    동물 이미지를 업로드하고 관련 정보를 반환합니다.
    
    Args:
        file (UploadFile): 업로드할 동물 이미지 파일
    
    Returns:
        UploadResponse: 파일 정보와 동물 정보를 포함한 응답
    
    Raises:
        HTTPException: 파일 처리 중 오류 발생 시
    """
    try:
        # 파일 타입 검증
        if not file.content_type.startswith("image/"):
            logger.error(f"Invalid file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an image."
            )

        # 파일 읽기
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )

        # 동물 이름 추출 및 검증
        animal_name = file.filename.split('.')[0].lower().strip()
        if not animal_name:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename. Animal name not found."
            )

        # 동물 정보 스크래핑
        try:
            animal_info = scrape_animal_info(animal_name)
            if not animal_info:
                logger.warning(f"No information found for animal: {animal_name}")
                animal_info = {"message": "No information available"}
        except Exception as e:
            logger.error(f"Error scraping animal info: {str(e)}")
            animal_info = {"error": "Failed to fetch animal information"}

        return UploadResponse(
            filename=file.filename,
            predicted_animal=animal_name,
            animal_info=animal_info,
            file_size=len(contents)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await file.close()

@router.get("/text/{animal_kr}", response_model=AnimalInfoResponse)
async def get_animal_info(animal_kr: str) -> AnimalInfoResponse:
    """
    한글 동물 이름으로 동물 정보를 조회합니다.
    
    Args:
        animal_kr (str): 한글 동물 이름
    
    Returns:
        AnimalInfoResponse: 번역된 이름과 동물 정보를 포함한 응답
    
    Raises:
        HTTPException: 정보 조회 중 오류 발생 시
    """
    try:
        # 입력 검증
        animal_kr = animal_kr.strip()
        if not animal_kr:
            raise HTTPException(
                status_code=400,
                detail="Animal name is required"
            )

        # 번역 및 정보 조회
        try:
            animal_en = korean_to_english(animal_kr)
            if not animal_en:
                raise HTTPException(
                    status_code=400,
                    detail="Could not translate animal name"
                )

            animal_info = scrape_animal_info(animal_en)
            if not animal_info:
                logger.warning(f"No information found for animal: {animal_en}")
                animal_info = {"message": "No information available"}

        except Exception as e:
            logger.error(f"Error processing animal info: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process animal information"
            )

        return AnimalInfoResponse(
            input=animal_kr,
            translated=animal_en,
            animal_info=animal_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_animal_info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
