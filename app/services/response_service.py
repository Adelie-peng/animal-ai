from typing import Dict
import requests
from dotenv import load_dotenv
import os


# .env 파일을 읽어들임
load_dotenv()


class ResponseService:
    def __init__(self):
        """Gemini API 키 로드"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key is None:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    def generate_prompt(self, animal_info: Dict[str, str]) -> str:
        """
        동물 정보를 기반으로 Gemini에 보낼 프롬프트 생성
        """
        name = animal_info.get("name", "알 수 없는 동물")
        description = animal_info.get("description", "설명이 없습니다.")
        habitat = animal_info.get("habitat", "서식지 정보가 없습니다.")

        prompt = (
            f"다음 동물 정보를 기반으로 사용자에게 친근하고 따뜻한 말투로 소개하는 문장을 작성해줘.\n\n"
            f"동물 이름: {name}\n"
            f"설명: {description}\n"
            f"서식지: {habitat}\n\n"
            f"추가 질문도 자연스럽게 유도해줘!"
        )

        return prompt

    def request_gemini(self, prompt: str) -> str:
        """
        Gemini API를 호출해서 답변 생성
        """
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.gemini_api_key}
        body = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, params=params, json=body)
        response.raise_for_status()

        candidates = response.json().get("candidates", [])
        if not candidates:
            return "답변을 생성하는 데 실패했어요!"

        return candidates[0]["content"]["parts"][0]["text"]

    def generate_response(self, animal_info: Dict[str, str]) -> str:
        """
        전체 과정: 프롬프트 생성 -> Gemini 호출 -> 자연스러운 답변 반환
        """
        prompt = self.generate_prompt(animal_info)
        response = self.request_gemini(prompt)
        return response
