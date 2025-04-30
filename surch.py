from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
from selenium.webdriver.common.keys import Keys
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://animalia.bio"
statuses = {
    "ne": "not-evaluated-ne",
    "dd": "data-deficient-dd",
    "lc": "least-concern-lc",
    "nt": "near-threatened-nt",
    "vu": "vulnerable-vu",
    "en": "endangered-en",
    "cr": "critically-endangered-cr",
    "ew": "extinct-in-the-wild-ew",
    "ex": "extinct-ex"
}

# Chrome 옵션 설정
options = Options()
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome(options=options)

# 한글 이름을 입력받고, 영어 이름으로 변환하는 함수
def find_english_name_by_korean(korean_name):
    for code, path in statuses.items():
        folder = os.path.join(os.getcwd(), f"animals_{code}")
        file_path = os.path.join(folder, "animals.txt")
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    en_name, ko_name = line.strip().split(" / ")
                    if ko_name == korean_name:
                        return en_name
    return None

# 사용자로부터 한글 이름을 입력받고 동물 정보로 이동
def move_to_animal_info(korean_name):
    english_name = find_english_name_by_korean(korean_name)
    
    if english_name:
        print(f"한글 이름 '{korean_name}'에 대한 영어 이름: {english_name}")
        
        # 영어 이름을 URL 슬러그로 변환하여 해당 동물 페이지로 이동
        url_slug = to_url_slug(english_name)
        driver.get(f"https://animalia.bio/ko/{url_slug}")
        time.sleep(3)
        print(f"동물 페이지로 이동: {driver.current_url}")
    else:
        print(f"한글 이름 '{korean_name}'을(를) 찾을 수 없습니다.")

# 이름을 URL용 슬러그로 변환 (공백은 -로, 작은따옴표는 없애기)
def to_url_slug(name):
    name = name.lower()  # 모두 소문자로 변환
    name = re.sub(r"[’'\",\.]", "", name)  # 작은 따옴표와 불필요한 기호 제거
    name = re.sub(r"\s+", "-", name)  # 공백은 -로 변환
    return name

# 테스트 예시: 한글로 질문을 받기
while True:
    korean_name = input("한글 동물 이름을 입력하세요 (종료하려면 'exit' 입력): ").strip()
    if korean_name.lower() == "exit":
        break
    move_to_animal_info(korean_name)

driver.quit()
