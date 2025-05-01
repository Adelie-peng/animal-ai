from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print("잠시만 기다리십시오…")
driver.get("https://ko.wikipedia.org/wiki/%EA%B0%80%EC%8B%9C%EC%98%AC%EB%B9%BC%EB%AF%B8")

# 페이지가 로드되도록 대기
try:
    # 페이지가 완전히 로드될 때까지 대기
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
    )

    # 페이지 소스를 가져오고 BeautifulSoup로 파싱
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # 동물 이름 추출
    name = soup.find("h1", {"id": "firstHeading"}).text.strip()

    # 동물 설명 추출 (여기선 첫 번째 문단을 예시로 추출)
    description_paragraph = soup.find("div", {"class": "reflist"})
    description = description_paragraph.find_previous("p").text.strip()

    print("✅ 동물 이름:", name)
    print("📄 설명:")
    print(description)

except Exception as e:
    print("❌ 오류 발생:", e)

driver.quit()
