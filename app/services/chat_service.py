# services/chat_service.py
import os
from dotenv import load_dotenv
import requests

# .env 파일 불러오기
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ChatBotService:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    def generate_response(self, animal_name: str, animal_info: str) -> str:
        """동물 이름과 정보를 받아 친근한 답변 생성"""
        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "key": self.api_key
        }
        prompt = (
            f"이 동물은 {animal_name}야!\n"
            f"이 동물에 대한 기본 정보는 다음과 같아:\n{animal_info}\n"
            f"친근하고 대화체로 설명해줘. 그리고 추가로 이 동물에 대해 궁금한 걸 하나 물어봐줘."
        )
        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        response = requests.post(self.api_url, headers=headers, params=params, json=body)

        if response.status_code == 200:
            result = response.json()
            # Gemini는 'candidates' 아래에 응답이 들어 있음
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "응답을 생성하는 데 문제가 발생했어."
        else:
            return f"Gemini API 호출 실패: {response.status_code} {response.text}"
