# services/chat_service.py
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import logging
import google.generativeai as genai
from dataclasses import dataclass

# 로거 설정
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv()  # .env 파일에서 환경 변수를 로드

@dataclass
class ChatError(Exception):
    """채팅 생성 과정에서 발생하는 예외를 처리하는 클래스"""
    message: str
    details: Optional[Dict] = None

class ChatBotService:
    def __init__(self):
        """Gemini API 서비스 초기화"""
        try:
            # .env 파일 로드
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables")
                raise ChatError("API 키를 찾을 수 없습니다.")

            # Gemini API 초기화
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("ChatBotService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChatBotService: {str(e)}")
            raise ChatError(f"서비스 초기화 실패: {str(e)}")

    def generate_response(self, animal_name: str, animal_info: Dict[str, str]) -> str:
        """
        동물 정보를 기반으로 친근한 응답을 생성합니다.
        
        Args:
            animal_name: 동물 이름
            animal_info: 동물 정보 딕셔너리
            
        Returns:
            str: 생성된 응답 메시지
            
        Raises:
            ChatError: 응답 생성 실패 시
        """
        try:
            # 프롬프트 템플릿 작성
            description = animal_info.get('description', '정보가 없습니다.')
            prompt = f"""**동물 정보**
이름: {animal_name}
설명: {description}

**요청사항**
위 동물에 대해 다음과 같이 설명해주세요:
1. 너무 유치하거나 어린이용 말투는 피하고, 자연스럽고 따뜻한 말투로 작성
2. 이 동물의 특징, 생태, 서식지 등 핵심 정보를 적절히 포함
3. 멸종 위험도에 따라 설명을 추가
4. 마지막에 흥미로운 질문을 하나 덧붙여 주세요

**응답**:"""

            # 응답 생성
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_k": 40,
                    "top_p": 0.95,
                    "max_output_tokens": 1024,
                }
            )

            if not response.text:
                logger.warning(f"Empty response received for {animal_name}")
                return "죄송해요, 지금은 답변을 생성하기 어려워요."

            logger.info(f"Successfully generated response for {animal_name}")
            return response.text

        except Exception as e:
            error_msg = f"Error generating response for {animal_name}: {str(e)}"
            logger.error(error_msg)
            raise ChatError(error_msg)

    def __del__(self):
        """리소스 정리"""
        try:
            # 필요한 경우 추가 정리 작업
            logger.info("ChatBotService resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
