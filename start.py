from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import openai

# ⛳️ OpenAI API 키 설정
openai.api_key = ''

def fetch_animal_info(url, output_file="animal_info.txt"):
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    print("🔍 동물 정보 수집 중...")
    driver.get(url)
    time.sleep(3)

    try:
        content = driver.find_element(By.CSS_SELECTOR, ".page-animal").text
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 동물 정보가 파일에 저장되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

def answer_question_from_file(question, info_file="animal_info.txt"):
    try:
        with open(info_file, "r", encoding="utf-8") as f:
            content = f.read()

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 동물에 대해 친절하고 정확하게 설명해주는 전문가입니다."},
                {"role": "user", "content": f"다음 동물 정보로 질문에 답하세요:\n\n{content}"},
                {"role": "user", "content": question}
            ]
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"❌ 오류 발생: {e}"

# === 실행 ===
if __name__ == "__main__":
    url = "https://animalia.bio/ko/BURROWING-OWL"
    fetch_animal_info(url)

    question = input("🤔 어떤 동물에 대해 알고 싶으세요? ")
    answer = answer_question_from_file(question)
    print("\n🧠 답변:", answer)
