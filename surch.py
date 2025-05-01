from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
from selenium.webdriver.common.keys import Keys
import re

# Chrome 옵션 설정
options = Options()
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(options=options)

# 한글 이름 -> 영어 이름 변환 딕셔너리 생성
def load_animal_names(file_path):
    animal_dict = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.strip():
                en_name, ko_name = line.strip().split(" / ")
                animal_dict[ko_name] = en_name
    return animal_dict

# 한글 이름을 입력받아 영어 이름을 찾아주는 함수
def get_english_name(ko_name, animal_dict):
    return animal_dict.get(ko_name, None)

# 한글 이름을 URL-friendly한 슬러그로 변환
def to_url_slug(name):
    name = name.lower()
    name = re.sub(r"[’'\",\.]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name

# 한글 이름 입력받기
ko_name_input = input("알고 싶은 동물의 한글 이름을 입력하세요: ")

# animals.txt에서 동물 이름 매핑
animal_dict = load_animal_names("animals.txt")

# 한글 이름에 해당하는 영어 이름 찾기
en_name = get_english_name(ko_name_input, animal_dict)

if en_name:
    print(f"입력한 한글 이름: {ko_name_input} -> 영어 이름: {en_name}")

    # 영어 이름을 URL로 변환
    url_slug = to_url_slug(en_name)
    url = f"https://animalia.bio/ko/{url_slug}"
    
    # 동물 정보 페이지로 이동
    driver.get(url)
    time.sleep(3)  # 페이지가 로드될 때까지 잠시 대기

    try:
        # 동물 정보가 있는 영역을 찾고 출력
        # 예시로 동물 이름을 출력하는 부분을 찾기
        animal_name_element = driver.find_element(By.CLASS_NAME, "a-h1")
        animal_name = animal_name_element.text.strip()
        
        # 추가적으로 필요한 정보를 가져올 수 있습니다.
        print(f"동물 이름: {animal_name}")
        
        # 추가 정보가 있다면 그 정보도 추출
        # 예: 설명, 분포 지역, 식습관 등
        description_element = driver.find_element(By.CLASS_NAME, "a-description")
        description = description_element.text.strip() if description_element else "설명 없음"
        
        print(f"설명: {description}")
    except Exception as e:
        print(f"동물 정보를 가져오는 데 실패했습니다: {e}")
else:
    print(f"입력한 한글 이름 '{ko_name_input}'에 해당하는 영어 이름을 찾을 수 없습니다.")

driver.quit()
