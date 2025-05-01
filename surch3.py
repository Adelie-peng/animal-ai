import os
import re
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, render_template, request

app = Flask(__name__)

import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"API 키: {GEMINI_API_KEY}")  # 디버깅용

import requests

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

headers = {"Content-Type": "application/json"}

data = {
    "contents": [
        {
            "parts": [{"text": "레드 울프에 대해 알려줘"}]
        }
    ]
}

res = requests.post(url, headers=headers, json=data)
print(res.json())

BASE_URL = "https://animalia.bio/ko/"
STATUSES = {
    "ne": "not-evaluated-ne", "dd": "data-deficient-dd", "lc": "least-concern-lc",
    "nt": "near-threatened-nt", "vu": "vulnerable-vu", "en": "endangered-en",
    "cr": "critically-endangered-cr", "ew": "extinct-in-the-wild-ew", "ex": "extinct-ex"
}

def find_english_name(korean_name):
    normalized_ko_name = normalize_string(korean_name)
    print(f"정규화된 한글 이름: {normalized_ko_name}")  # 디버깅 출력
    
    for code in STATUSES:
        path = os.path.join(f"animals_{code}", "animals.txt")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if " : " in line:
                        ko, en = line.strip().split(" : ")
                        normalized_en_name = normalize_string(en)
                        normalized_ko_name_from_file = normalize_string(ko)
                        
                        print(f"파일 내 한글 이름: {normalized_ko_name_from_file}, 영어 이름: {normalized_en_name}")  # 디버깅 출력
                        
                        if normalized_ko_name == normalized_ko_name_from_file:
                            return en
    return None


def normalize_string(input_str):
    """한글과 영어 이름을 비교하기 위한 정규화 함수"""
    # 특수문자 제거하고 소문자로 변환, 공백도 처리
    return re.sub(r"[^\w\s]", "", input_str.strip().lower())

def find_english_name(korean_name):
    normalized_ko_name = normalize_string(korean_name)

    for code in STATUSES:
        path = os.path.join(f"animals_{code}", "animals.txt")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if " / " in line:
                        en, ko = line.strip().split(" / ")
                        normalized_en_name = normalize_string(en)
                        normalized_ko_name_from_file = normalize_string(ko)

                        if normalized_ko_name == normalized_ko_name_from_file:
                            return en
    return None


from selenium.webdriver.chrome.service import Service  # 이 라인도 꼭 추가

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_and_save_animal_info(url, filename="animal_info.txt"):
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    
    try:
        # s-char-text 클래스가 나타날 때까지 최대 10초 기다림
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "s-char-text"))
        )
        content = element.text
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        content = f"오류: {e}"
    finally:
        driver.quit()
    return content


def get_gemini_answer(question, context_file="animal_info.txt"):
    with open(context_file, encoding="utf-8") as f:
        context = f.read()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"이 동물 정보로 다음 질문에 답해줘:\n\n{context}\n\n{question}"}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"❌ Gemini API 오류: {response.text}"


@app.route("/", methods=["GET", "POST"])
def index():
    answer = ""
    if request.method == "POST":
        ko_name = request.form["korean_name"]
        question = request.form["question"]
        print(find_english_name(ko_name))

        en_name = find_english_name(ko_name)
        if not en_name:
            answer = "❌ 해당 동물 이름을 찾을 수 없습니다."
        else:
            slug = re.sub(r"[’'\",\.]", "", en_name).lower().replace(" ", "-")
            url = f"{BASE_URL}{slug}"
            fetch_and_save_animal_info(url)
            answer = get_gemini_answer(question)

    return render_template("index.html", answer=answer)



if __name__ == "__main__":
    app.run(debug=True)
