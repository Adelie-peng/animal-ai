from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import time



from selenium.webdriver.common.keys import Keys

# 브라우저 꺼짐 방지 옵션 (선택)
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# driver = webdriver.Chrome(options=chrome_options)
# driver.maximize_window()  # 또는 set_window_size(1200, 1000)
# driver.get("https://animalia.bio/ko/not-evaluated")

# # 페이지 전체 로딩 대기
# time.sleep(3)

# while True:
#     try:
#         # 페이지 가장 아래로 스크롤
#         driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
#         time.sleep(2)

#         # "더 보기" 버튼 찾기
#         load_more = driver.find_element(By.CLASS_NAME, "load-more")

#         # 스크롤해서 버튼이 보이게 만들기
#         driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
#         time.sleep(1)

#         # 버튼 클릭
#         load_more.click()
#         print("더 보기 버튼 클릭됨")
#         time.sleep(3)
        
#     except Exception as e:
#         print("모든 동물 데이터를 로드했거나 버튼이 없습니다.")
#         break

# 로드된 동물 이름 수집
# animal_elements = driver.find_elements(By.CLASS_NAME, "f-h2")
# animal_names = [el.text.strip() for el in animal_elements if el.text.strip()]
# print(f"총 수집된 동물 수: {len(animal_names)}")
# for name in animal_names:
#     print(name)

# driver.quit()

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

for code, path in statuses.items():
    url = f"{BASE_URL}/{path}"
    driver.get(url)
    time.sleep(3)

    # "더 로드" 버튼을 계속 클릭해서 모든 항목 로드
    # while True:
    #     try:
    #         load_more = driver.find_element(By.CSS_SELECTOR, ".btn-more")
    #         driver.execute_script("arguments[0].click();", load_more)
    #         print("더 로드 클릭")
    #         time.sleep(2)
    #     except:
    #         print("더 로드 없음 또는 더 이상 없음")
    #         break
    
    while True:
        try:
            # 페이지 가장 아래로 스크롤
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(2)

            # "더 보기" 버튼 찾기
            load_more = driver.find_element(By.CLASS_NAME, "load-more")

            # 스크롤해서 버튼이 보이게 만들기
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
            time.sleep(1)

            # 버튼 클릭
            load_more.click()
            print("더 보기 버튼 클릭됨")
            time.sleep(3)
            
        except Exception as e:
            print("모든 동물 데이터를 로드했거나 버튼이 없습니다.")
            break

        # 모든 동물 이름 추출 (class="f-h2")
        animal_elements = driver.find_elements(By.CLASS_NAME, "f-h2")
        animal_names = [el.text.strip() for el in animal_elements if el.text.strip()]

        # 폴더 저장
        folder = os.path.join(os.getcwd(), f"animals_{code}")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "animals.txt"), "w", encoding="utf-8") as f:
            for name in animal_names:
                f.write(name + "\n")

        print(f"[{code.upper()}] 동물 수집 완료: {len(animal_names)}마리 저장됨\n")

animal_elements = driver.find_elements(By.CLASS_NAME, "f-h2")
animal_names = [el.text.strip() for el in animal_elements if el.text.strip()]
print(f"총 수집된 동물 수: {len(animal_names)}")
for name in animal_names:
    print(name)

driver.quit()
