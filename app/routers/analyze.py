from fastapi import APIRouter, UploadFile, File
from app.services.sam_service import sam_service
from services.classifier_service import AnimalClassifier
from services.db_service import AnimalDatabase
from services.chat_service import ChatBotService
from PIL import Image
import numpy as np
import io

router = APIRouter()

# 서비스 인스턴스
classifier = AnimalClassifier()
db_service = AnimalDatabase()
chatbot_service = ChatBotService()

@router.post("/analyze/")
async def analyze_animal(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")

    # 여기서는 적절한 포인트가 있어야 작동하지만, 샘플 호출용이라면 더미 포인트 사용 가능
    input_point = (512, 512)  # 예시
    _, mask, _ = sam_service.segment(image_path=file.file, input_point=input_point)

    classification_result = classifier.classify_animal(image, mask)
    animal_class = classification_result["class"]
    confidence = classification_result["confidence"]
    top3 = classification_result["top3"]

    animal_info = db_service.get_info(animal_class)
    friendly_message = chatbot_service.generate_response(animal_class, animal_info)

    return {
        "animal": animal_class,
        "confidence": confidence,
        "top3_predictions": top3,
        "info": animal_info,
        "friendly_message": friendly_message,
    }
