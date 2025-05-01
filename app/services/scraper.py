# app/services/scraper.py
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
import papago  # 필요 시 Papago API 또는 다른 번역 서비스 사용 (pip install papago)

# 로거 설정
logger = logging.getLogger(__name__)

def korean_to_english(animal_kr: str) -> Optional[str]:
    """
    한글 동물 이름을 영어로 번역
    
    Args:
        animal_kr (str): 한글 동물 이름
        
    Returns:
        Optional[str]: 영어 동물 이름 또는 None (실패 시)
    """
    try:
        # 간단한 사전 (실제로는 번역 API 사용 권장)
        translation_dict = {
            "개": "dog",
            "강아지": "dog",
            "고양이": "cat",
            "사자": "lion",
            "호랑이": "tiger",
            "곰": "bear",
            "말": "horse",
            "판다": "panda",
            "여우": "fox",
            "토끼": "rabbit",
            "사슴": "deer",
            "늑대": "wolf",
            "원숭이": "monkey",
            "코끼리": "elephant",
            "기린": "giraffe",
            "얼룩말": "zebra",
            "펭귄": "penguin"
        }
        
        # 사전에서 번역 시도
        if animal_kr in translation_dict:
            return translation_dict[animal_kr]
            
        # 여기에 Papago API 호출 코드 추가 (필요 시)
        # 예: return papago.translate(animal_kr, source='ko', target='en')
            
        logger.warning(f"Translation not found for: {animal_kr}")
        return None
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return None

def scrape_animal_info(animal_en: str) -> Dict[str, str]:
    """
    동물 정보를 웹에서 스크래핑
    
    Args:
        animal_en (str): 영어 동물 이름
        
    Returns:
        Dict[str, str]: 동물 정보 (description, habitat 등)
    """
    try:
        # 실제 프로젝트에서는 크롤링 대신 DB를 사용하는 것을 권장
        # 여기에서는 간단한 샘플 데이터 반환
        animal_data = {
            "dog": {
                "description": "개는 인간과 가장 오랫동안 함께한 반려동물입니다. 충성심이 강하고 다양한 품종이 있으며, 인간과의 깊은 유대감을 형성합니다.",
                "habitat": "전 세계적으로 인간과 함께 생활하며, 다양한 환경에 적응할 수 있습니다.",
                "lifespan": "10-13년",
                "diet": "잡식성"
            },
            "cat": {
                "description": "고양이는 독립적인 성격을 가진 우아한 반려동물입니다. 사냥 본능이 강하고, 깨끗한 것을 좋아하며 자신만의 영역을 중요시합니다.",
                "habitat": "전 세계 거의 모든 곳에서 인간과 함께 살고 있으며, 도시와 시골 환경 모두에 적응합니다.",
                "lifespan": "12-18년",
                "diet": "육식성"
            },
            "lion": {
                "description": "사자는 '동물의 왕'으로 불리는 대형 고양이과 동물입니다. 무리를 이루어 생활하며 수컷은 특유의 갈기를 가지고 있습니다.",
                "habitat": "아프리카 초원과 사바나에 주로 서식합니다.",
                "lifespan": "10-14년",
                "diet": "육식성"
            },
            "tiger": {
                "description": "호랑이는 고양이과에서 가장 큰 동물로, 강력한 근육과 특유의 줄무늬가 특징입니다. 단독 생활을 하며 영역을 중요시합니다.",
                "habitat": "아시아 지역의 다양한 서식지에 분포하지만, 현재는 멸종 위기에 처해 있습니다.",
                "lifespan": "10-15년",
                "diet": "육식성"
            }
        }
        
        # 동물 이름 정리 (a, the 등 제거)
        animal_clean = animal_en.lower().replace("a ", "").replace("the ", "").strip()
        
        # 데이터베이스에서 정보 조회
        if animal_clean in animal_data:
            return animal_data[animal_clean]
        
        # 실제 웹 크롤링을 수행할 경우 (예시)
        # url = f"https://animalia.bio/ko/{animal_clean}"
        # response = requests.get(url)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # description = soup.select_one('.description').text
        # habitat = soup.select_one('.habitat').text
        # ...
            
        logger.warning(f"No information found for: {animal_en}")
        return {"description": f"{animal_en}에 대한 정보를 찾을 수 없습니다."}
        
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return {"error": f"정보를 가져오는 중 오류 발생: {str(e)}"}