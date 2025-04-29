# 업로드 + 예측 처리
# Upload + Predict 샘플

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.model import segment_animal

router = APIRouter()

@router.post("/predict")
async def predict_animal(file: UploadFile = File(...)):
    contents = await file.read()

    # segment_animal 함수 호출 (MobileSAM 사용)
    segmented_image_info = segment_animal(contents)

    return JSONResponse(content={
        "segmented_info": segmented_image_info
    })
