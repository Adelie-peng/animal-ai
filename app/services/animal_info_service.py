from typing import Dict

# 샘플 데이터베이스 (실제로는 DB 연결로 대체 가능)
ANIMAL_DATABASE = {
    "a dog": {
        "name": "개",
        "description": "개의 평균 수명은 10~13년이며, 충성심이 강하고 다양한 품종이 있습니다.",
        "habitat": "가정, 야생"
    },
    "a cat": {
        "name": "고양이",
        "description": "고양이는 독립적인 성격을 가진 반려동물로, 사냥 본능이 강합니다.",
        "habitat": "가정, 야생"
    },
    "a lion": {
        "name": "사자",
        "description": "사자는 '숲의 왕'으로 불리며, 주로 아프리카 초원에서 서식합니다.",
        "habitat": "초원"
    },
    # 필요한 만큼 추가 가능
}

class AnimalInfoService:
    def __init__(self):
        self.database = ANIMAL_DATABASE

    def get_info(self, animal_class: str) -> Dict[str, str]:
        """
        동물 클래스를 입력받아 관련 정보를 반환
        Args:
            animal_class (str): CLIP이 분류한 동물 클래스 (ex. "a dog")
        Returns:
            Dict[str, str]: 동물 정보 (name, description, habitat)
        """
        info = self.database.get(animal_class)
        if not info:
            return {
                "name": "알 수 없음",
                "description": "데이터베이스에 정보가 없습니다.",
                "habitat": "정보 없음"
            }
        return info
