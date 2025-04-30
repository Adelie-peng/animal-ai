from typing import Dict, Optional, TypedDict
import logging
from dataclasses import dataclass

# 로거 설정
logger = logging.getLogger(__name__)

# 타입 정의
class AnimalInfo(TypedDict):
    name: str
    description: str
    habitat: str
    average_lifespan: Optional[str]
    diet: Optional[str]

# 샘플 데이터베이스 (실제로는 DB 연결로 대체 가능)
ANIMAL_DATABASE: Dict[str, AnimalInfo] = {
    "a dog": {
        "name": "개",
        "description": "개의 평균 수명은 10~13년이며, 충성심이 강하고 다양한 품종이 있습니다.",
        "habitat": "가정, 야생",
        "average_lifespan": "10-13년",
        "diet": "잡식성"
    },
    "a cat": {
        "name": "고양이",
        "description": "고양이는 독립적인 성격을 가진 반려동물로, 사냥 본능이 강합니다.",
        "habitat": "가정, 야생",
        "average_lifespan": "12-18년",
        "diet": "육식성"
    },
    "a lion": {
        "name": "사자",
        "description": "사자는 '숲의 왕'으로 불리며, 주로 아프리카 초원에서 서식합니다.",
        "habitat": "초원",
        "average_lifespan": "10-14년",
        "diet": "육식성"
    }
}

@dataclass
class AnimalNotFoundError(Exception):
    animal_class: str
    message: str = "동물 정보를 찾을 수 없습니다"

class AnimalInfoService:
    """동물 정보 서비스 클래스"""
    
    def __init__(self):
        """AnimalInfoService 초기화"""
        self.database = ANIMAL_DATABASE
        logger.info("AnimalInfoService initialized with database")

    def get_info(self, animal_class: str) -> AnimalInfo:
        """
        동물 클래스를 입력받아 관련 정보를 반환합니다.

        Args:
            animal_class (str): CLIP이 분류한 동물 클래스 (ex. "a dog")

        Returns:
            AnimalInfo: 동물 정보 (name, description, habitat, average_lifespan, diet)

        Raises:
            AnimalNotFoundError: 데이터베이스에서 동물 정보를 찾을 수 없는 경우
        """
        try:
            # 입력값 전처리
            animal_class = animal_class.lower().strip()
            
            # 데이터베이스에서 정보 조회
            info = self.database.get(animal_class)
            if not info:
                logger.warning(f"Animal info not found for: {animal_class}")
                raise AnimalNotFoundError(animal_class)

            logger.info(f"Successfully retrieved info for: {animal_class}")
            return info

        except Exception as e:
            logger.error(f"Error getting animal info: {str(e)}")
            return AnimalInfo(
                name="알 수 없음",
                description="데이터베이스에서 정보를 찾을 수 없습니다.",
                habitat="정보 없음",
                average_lifespan=None,
                diet=None
            )

    def add_animal(self, animal_class: str, info: AnimalInfo) -> None:
        """
        새로운 동물 정보를 데이터베이스에 추가합니다.

        Args:
            animal_class (str): 동물 클래스명
            info (AnimalInfo): 동물 정보
        """
        try:
            animal_class = animal_class.lower().strip()
            self.database[animal_class] = info
            logger.info(f"Added new animal info: {animal_class}")
        except Exception as e:
            logger.error(f"Error adding animal info: {str(e)}")
            raise
