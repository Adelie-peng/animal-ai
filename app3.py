from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
from selenium.webdriver.common.keys import Keys
import re  # 정규식을 사용하여 숫자만 추출
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

MAX_COUNT = 40  # 동물 이름 수집 최대 개수를 40개로 설정

# 이름을 URL용 슬러그로 변환
def to_url_slug(name):
    name = name.lower()
    name = re.sub(r"[’'\",\.]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name

for code, path in statuses.items():
    folder = os.path.join(os.getcwd(), f"animals_{code}")
    file_path = os.path.join(folder, "animals.txt")

    # 폴더가 없다면 생성
    os.makedirs(folder, exist_ok=True)

    # 파일이 존재하면, 저장된 동물 이름 수 확인
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            animal_names = f.readlines()
            animal_names = [name.strip() for name in animal_names if name.strip()]  # 불필요한 공백 제거
            current_animal_count = len(animal_names)
    else:
        animal_names = []
        current_animal_count = 0  # 파일이 없으면 동물 이름 개수는 0

    # 동물 수를 페이지에서 가져오기
    url = f"{BASE_URL}/{path}"
    driver.get(url)
    time.sleep(3)

    # 페이지에서 '20 종'과 같은 동물 수를 추출
    try:
        title_text = driver.find_element(By.CLASS_NAME, "title").find_element(By.TAG_NAME, "h2").text
        animal_count = int(re.search(r"\d+", title_text).group())  # 숫자만 추출하여 정수로 변환
        print(f"[{code.upper()}] 동물 수: {animal_count}마리")
    except Exception as e:
        print(f"[{code.upper()}] 동물 수를 가져오는데 실패했습니다. 예외: {e}")
        animal_count = 0  # 예외가 발생하면 0으로 설정하여 계속 진행

    # 동물 수가 현재 저장된 수와 동일하거나 40개 이상이면 해당 카테고리 스킵
    if animal_count == current_animal_count or current_animal_count >= MAX_COUNT:
        print(f"[{code.upper()}] 이미 {current_animal_count}개의 동물이 저장되어 있어 해당 카테고리를 스킵합니다.")
        continue

    print(f"[{code.upper()}] 데이터 수집 시작")

    # 동물 이름 수집 시작
    while True:
        # 동물 이름 추출 (class="f-h2")
        animal_elements = driver.find_elements(By.CLASS_NAME, "f-h2")
        new_animal_names = [el.text.strip() for el in animal_elements if el.text.strip()]

        if new_animal_names:
            print(f"[{code.upper()}] 수집된 동물 이름 {len(new_animal_names)}개")
        else:
            print(f"[{code.upper()}] 동물 이름이 수집되지 않았습니다. 페이지를 확인해주세요.")

        # 새로운 동물 이름 중 중복되지 않은 이름만 추가
        for name in new_animal_names:
            if current_animal_count < MAX_COUNT:
                if name.strip() not in animal_names:  # 이름 앞뒤 공백도 제거하고 비교
                    animal_names.append(name.strip())  # 추가 시 공백을 제거하고 저장
                    current_animal_count += 1
            else:
                print(f"[{code.upper()}] 40개 이름 수집 완료, 카테고리 스킵")
                break  # 40개 이름이 수집되었으면 바로 해당 카테고리를 건너뜀

        # 40개가 다 채워지면 더 이상 동물 이름을 추가하지 않음
        if current_animal_count >= MAX_COUNT:
            print(f"[{code.upper()}] 40개 이름 수집 완료, 다음 등급으로 넘어갑니다.")
            break

        # 페이지 가장 아래로 스크롤
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(2)

        # "더 보기" 버튼이 있으면 클릭
        try:
            load_more = driver.find_element(By.CLASS_NAME, "load-more")
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
            time.sleep(1)
            load_more.click()
            print("더 보기 버튼 클릭됨")
            time.sleep(3)
        except Exception as e:
            print("모든 동물 데이터를 로드했거나 버튼이 없습니다.")
            break

    # 한글 이름 수집
    for en_name in animal_names[:MAX_COUNT]:
        url_slug = to_url_slug(en_name)
        driver.get(f"https://animalia.bio/ko/{url_slug}")
        try:
            ko_name_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "a-h1"))
            )
            ko_name = ko_name_element.text.strip()
        except:
            ko_name = "한글 이름 없음"

        # 파일에 영어와 한글 이름을 저장
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"{en_name} / {ko_name}\n")
            print(f"[{code.upper()}] {en_name} / {ko_name}")
        except Exception as e:
            print(f"[{code.upper()}] 파일 작성 중 오류: {e}")

    print(f"[{code.upper()}] 동물 수집 완료: {len(animal_names[:MAX_COUNT])}마리 저장됨\n")

driver.quit()
