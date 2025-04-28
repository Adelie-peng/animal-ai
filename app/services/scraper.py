# 스크래핑 + 한글/영어 변환 유틸

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# 한글 ➔ 영어 변환 (간단 매핑)
def korean_to_english(animal_kr: str) -> str:
    dictionary = {
        "사자": "lion",
        "호랑이": "tiger",
        "코끼리": "elephant",
        "여우": "fox",
        "늑대": "wolf",
        "고양이": "cat",
        "개": "dog",
    }
    return dictionary.get(animal_kr, animal_kr)

# animalia.bio에서 동물 설명 스크래핑
def scrape_animal_info(animal_en: str) -> str:
    url = f"https://animalia.bio/ko/{quote(animal_en)}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        desc = soup.find("div", {"class": "field-body"})

        if desc:
            return desc.text.strip()
        else:
            return "동물 정보를 찾을 수 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"
