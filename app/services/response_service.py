from typing import Dict, Optional
import requests
from dotenv import load_dotenv
import os
import logging
from functools import lru_cache
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util import Retry  # 변경된 import 문

# 로거 설정
logger = logging.getLogger(__name__)

@dataclass
class ResponseError(Exception):
    """응답 생성 과정에서 발생하는 예외를 처리하는 클래스"""
    message: str
    details: Optional[Dict] = None

class ResponseService:
    """Gemini API를 사용한 동물 소개 응답 생성 서비스"""

    def __init__(self):
        """서비스 초기화 및 API 키 설정"""
        try:
            # .env 파일 로드
            load_dotenv()
            
            # API 키 검증
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

            # HTTP 세션 설정
            self.session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            )
            self.session.mount('https://', HTTPAdapter(max_retries=retry_strategy))
            
            # API 엔드포인트 설정
            self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            
            logger.info("ResponseService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ResponseService: {str(e)}")
            raise ResponseError("서비스 초기화 실패", {"error": str(e)})

    def generate_prompt(self, animal_info: Dict[str, str]) -> str:
        """
        동물 정보를 기반으로 Gemini에 보낼 프롬프트 생성
        
        Args:
            animal_info: 동물 정보 딕셔너리
            
        Returns:
            str: 생성된 프롬프트
        """
        try:
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
            
            logger.debug(f"Generated prompt for animal: {name}")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to generate prompt: {str(e)}")
            raise ResponseError("프롬프트 생성 실패", {"error": str(e)})

    @lru_cache(maxsize=100)
    def request_gemini(self, prompt: str) -> str:
        """
        Gemini API를 호출해서 답변 생성
        
        Args:
            prompt: API에 전달할 프롬프트
            
        Returns:
            str: 생성된 답변
            
        Raises:
            ResponseError: API 호출 실패 시
        """
        try:
            headers = {"Content-Type": "application/json"}
            params = {"key": self.api_key}
            body = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }
            
            response = self.session.post(
                self.api_url,
                headers=headers,
                params=params,
                json=body,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            candidates = data.get("candidates", [])
            
            if not candidates:
                logger.warning("No response candidates from Gemini API")
                return "답변을 생성하는 데 실패했어요!"

            generated_text = candidates[0]["content"]["parts"][0]["text"]
            logger.info("Successfully generated response from Gemini API")
            return generated_text

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise ResponseError("API 요청 실패", {"error": str(e)})
            
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            raise ResponseError("예기치 않은 오류", {"error": str(e)})

    def generate_response(self, animal_info: Dict[str, str]) -> str:
        """
        전체 과정: 프롬프트 생성 -> Gemini 호출 -> 자연스러운 답변 반환
        
        Args:
            animal_info: 동물 정보 딕셔너리
            
        Returns:
            str: 생성된 최종 응답
        """
        try:
            prompt = self.generate_prompt(animal_info)
            response = self.request_gemini(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return "죄송해요, 응답을 생성하는 중에 문제가 발생했어요."

    def __del__(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {str(e)}")
