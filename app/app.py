from fastapi import FastAPI
from app.routers import analyze

app = FastAPI()
app.include_router(analyze.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API is alive"}

# from fastapi import FastAPI, UploadFile, File
# from app.routers import analyze
# from PIL import Image
# import numpy as np
# import io

# app = FastAPI()
# app.include_router(analyze.router, prefix="/api")

# @app.get("/")
# def root():
#     return {"message": "API is alive"}

# @app.post("/analyze")
# async def analyze_animal(file: UploadFile = File(...)):
#     # 파일 읽기
#     contents = await file.read()
#     image = Image.open(io.BytesIO(contents)).convert("RGB")
    
#     # 1. Segmentation
#     mask = sam_service.segment(image)
    
#     # 2. Classification
#     classification_result = classifier.classify_animal(image, mask)
    
#     # 3. Database 조회
#     animal_name = classification_result["class"].replace("a ", "").strip()
#     animal_info = database.get_animal_info(animal_name)
    
#     # 4. Gemini 답변 생성
#     final_message = response_service.generate_response(animal_info)
    
#     return {
#         "predicted_class": animal_name,
#         "confidence": classification_result["confidence"],
#         "description": animal_info,
#         "message": final_message
#     }
