from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# 크롬 드라이버 설정
options = Options()
options.headless = True  # 창을 띄우지 않고 실행
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# URL 설정 (BURROWING OWL 페이지)
url = "https://animalia.bio/ko/BURROWING-OWL"
driver.get(url)

# 페이지 로딩 대기
time.sleep(3)

# 필요한 부분을 찾아서 내용 추출
try:
    # s-char-text 클래스 내에서 텍스트를 찾기
    content_section = driver.find_element(By.CSS_SELECTOR, ".s-char-text")
    animal_description = content_section.text  # s-char-text 클래스의 텍스트 저장

    # 데이터를 파일로 저장
    with open("animal_description.txt", "w", encoding="utf-8") as file:
        file.write(animal_description)
    print("동물 정보가 파일에 저장되었습니다.")

except Exception as e:
    print(f"오류 발생: {e}")

# 크롬 드라이버 종료
driver.quit()

import openai  # OpenAI GPT 모델을 사용한 예시
import os

# OpenAI API 키 설정 (자신의 API 키를 입력해야 합니다)
openai.api_key = 'AIzaSyD7tltWlHy_qlv01v9aQI_b6jyDKwCWL-g'

# 텍스트 데이터를 읽어서 챗봇에서 사용하도록 하는 함수
def get_animal_info(query):
    try:
        # 동물 데이터 파일 열기
        with open("animal_description.txt", "r", encoding="utf-8") as file:
            animal_text = file.read()

        # GPT 모델을 이용해 질문에 대한 답변 생성
        response = openai.Completion.create(
            engine="text-davinci-003",  # 최신 모델 사용 (필요에 따라 다를 수 있음)
            prompt=f"다음 텍스트를 기반으로 {query}에 대해 설명해 주세요:\n{animal_text}",
            max_tokens=200
        )
        
        return response.choices[0].text.strip()
    
    except Exception as e:
        return f"오류가 발생했습니다: {e}"

# 챗봇에 질문 입력
query = input("어떤 동물에 대해 알고 싶으세요? ")

# 답변 출력
response = get_animal_info(query)
print(f"답변: {response}")
