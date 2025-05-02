# services/db_service.py

from typing import Dict, Optional
import logging

# 로거 설정
logger = logging.getLogger(__name__)

class AnimalDatabase:
    def __init__(self):
        """간단한 in-memory database"""
        self.database: Dict[str, Dict[str, str]] = {
            animal: {"description": desc} 
            for animal, desc in {
                "dog": "강아지는 인간과 가장 친숙한 반려동물이에요. 충성심이 강하고 다양한 품종이 있죠!",
                "cat": "고양이는 독립적이면서도 사랑스러운 성격을 가진 동물이에요. 가끔은 츤데레 매력을 보여줘요.",
                "lion": "사자는 '동물의 왕'이라고 불리죠. 야생의 상징이에요!",
                "tiger": "호랑이는 강력한 힘과 아름다운 줄무늬를 가진 멋진 포식자에요.",
                "bear": "곰은 크고 강하지만 의외로 귀여운 면도 많아요. 겨울잠을 자는 특징이 있어요.",
                "horse": "말은 빠르고 우아한 동물이에요. 인간과 오랫동안 함께한 친구죠.",
                "panda": "판다는 대나무를 좋아하는 귀여운 동물이에요. 느긋한 성격으로 유명해요.",
                "fox": "여우는 영리하고 민첩한 동물이에요. 빨간 털과 뾰족한 귀가 특징이에요.",
                "rabbit": "토끼는 부드럽고 빠른 동물이에요. 당근을 좋아할 것 같지만 실제로는 풀을 더 좋아해요.",
                "deer": "사슴은 우아하고 민첩한 초식동물이에요. 아름다운 뿔을 가진 종도 많아요.",
                "wolf": "늑대는 사회적이고 협력적인 동물이에요. 무리 생활을 통해 강력함을 발휘하죠.",
                "monkey": "원숭이는 영리하고 장난기가 많은 동물이에요. 나무타기에 능숙해요.",
                "elephant": "코끼리는 육지에서 가장 큰 동물이에요. 뛰어난 기억력을 가지고 있어요.",
                "giraffe": "기린은 세상에서 가장 목이 긴 동물이에요. 높은 나뭇잎을 먹어요.",
                "zebra": "얼룩말은 독특한 줄무늬를 가진 초식동물이에요. 각자 줄무늬 패턴이 달라요.",
                "penguin": "펭귄은 날지 못하지만, 수영을 잘하는 새에요. 귀여운 외모로 사랑받고 있어요.",
            }.items()
        }
        logger.info("AnimalDatabase initialized successfully")

    def get_info(self, animal_class: str) -> Dict[str, str]:
        """
        동물 정보를 딕셔너리 형태로 반환
        
        Args:
            animal_class (str): 동물 클래스명 (예: "a dog" -> "dog")
        
        Returns:
            Dict[str, str]: 동물 정보를 담은 딕셔너리
        """
        try:
            # 입력값 전처리
            animal_class = animal_class.lower().strip()
            if animal_class.startswith("a "):
                animal_class = animal_class[2:]
            
            info = self.database.get(animal_class)
            if not info:
                logger.warning(f"No information found for: {animal_class}")
                return {"message": "정보를 찾을 수 없습니다"}
                
            return info
            
        except Exception as e:
            logger.error(f"Error retrieving animal info: {str(e)}")
            return {"error": "데이터베이스 조회 중 오류가 발생했습니다"}