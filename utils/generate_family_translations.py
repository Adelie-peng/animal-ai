# utils/generate_family_translations.py
import sqlite3
import re
from pathlib import Path
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 데이터베이스 경로
ROOT_PATH = Path(__file__).parent.parent
DB_PATH = ROOT_PATH / 'data' / 'database' / 'animal_data.db'

def extract_family_names():
    """
    데이터베이스에서 동물 이름 패턴을 분석하여 과(Family) 수준의 매핑 추출
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 1. 모든 동물 이름 가져오기
    cursor.execute("SELECT name_en, name_ko FROM animals")
    all_animals = cursor.fetchall()
    
    # 2. 과 수준 후보 패턴 찾기
    family_patterns = {}
    ko_patterns = {}
    
    for en_name, ko_name in all_animals:
        # 영어 이름에서 단어 추출
        en_words = en_name.lower().split()
        
        # 마지막 단어가 종종 과 수준의 이름 (예: "SIKA DEER" -> "deer")
        if len(en_words) > 1:
            family_word = en_words[-1]
            
            # 패턴 카운트 증가
            family_patterns[family_word] = family_patterns.get(family_word, 0) + 1
            
            # 한글 이름에서 패턴 찾기
            if ko_name:
                # '사슴', '토끼'와 같은 패턴 찾기
                for common_suffix in ['사슴', '토끼', '고래', '호랑이', '늑대', '여우', '펭귄', '코끼리', '원숭이', '독수리']:
                    if common_suffix in ko_name:
                        ko_patterns[family_word] = ko_patterns.get(family_word, []) + [common_suffix]
    
    # 3. 유효한 과 수준 매핑 생성
    family_mappings = {}
    
    # 특정 횟수 이상 반복되는 패턴만 선택
    min_occurrences = 2
    for family_word, count in family_patterns.items():
        if count >= min_occurrences:
            # 한글 매핑 찾기
            if family_word in ko_patterns:
                # 가장 자주 나오는 한글 패턴 선택
                ko_options = ko_patterns[family_word]
                if ko_options:
                    most_common = max(set(ko_options), key=ko_options.count)
                    family_mappings[family_word] = most_common
    
    # 4. 결과 출력 및 반환
    logger.info(f"총 {len(family_mappings)}개의 과(Family) 수준 매핑 발견:")
    for en, ko in family_mappings.items():
        logger.info(f"  {en} -> {ko}")
    
    # 5. 추가 수동 매핑 (자동 추출이 어려운 경우)
    manual_mappings = {
        "dog": "개",
        "cat": "고양이",
        "bear": "곰",
        "deer": "사슴",
        "rabbit": "토끼",
        "lion": "사자",
        "tiger": "호랑이",
        "wolf": "늑대",
        "fox": "여우",
        "whale": "고래",
        "dolphin": "돌고래",
        "monkey": "원숭이",
        "elephant": "코끼리",
        "giraffe": "기린",
        "zebra": "얼룩말",
        "penguin": "펭귄",
        "eagle": "독수리",
        "owl": "올빼미",
        "snake": "뱀",
        "turtle": "거북이",
        "crocodile": "악어",
        "frog": "개구리",
        "mouse": "생쥐"
    }
    
    # 수동 매핑을 자동 매핑과 병합
    for en, ko in manual_mappings.items():
        if en not in family_mappings:
            family_mappings[en] = ko
            logger.info(f"  수동 추가: {en} -> {ko}")
    
    # 6. 데이터베이스에 매핑 저장
    for en_name, ko_name in family_mappings.items():
        # 기본 설명 생성
        description = f"{ko_name}은(는) 다양한 종류가 있는 동물입니다."
        
        # 데이터베이스에 추가
        cursor.execute('''
        INSERT OR IGNORE INTO animals (name_en, name_ko, description)
        VALUES (?, ?, ?)
        ''', (en_name, ko_name, description))
        
        cursor.execute('''
        INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
        VALUES (?, ?)
        ''', (ko_name, en_name))
    
    conn.commit()
    logger.info(f"총 {len(family_mappings)}개의 과(Family) 수준 매핑이 데이터베이스에 저장되었습니다.")
    
    conn.close()
    return family_mappings

if __name__ == "__main__":
    extract_family_names()
    