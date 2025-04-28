# 업로드 + 예측 처리
# Upload + Predict 샘플

from fastapi import APIRouter, UploadFile, File
from app.services import model

router = APIRouter()

@router.post("/predict")
async def predict_animal(file: UploadFile = File(...)):
    contents = await file.read()
    result = model.predict(contents)  # 모델 인퍼런스 호출
    return {"animal": result}
