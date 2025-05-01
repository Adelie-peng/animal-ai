import os
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.keys import Keys
import re  # 정규식을 사용하여 숫자만 추출
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("iucn_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IUCNCrawler")

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

# SQLite 데이터베이스 설정
def setup_database():
    """
    데이터베이스 연결 및 테이블 생성
    
    Returns:
        tuple: (연결 객체, 커서 객체)
    """
    # 프로젝트 루트 기준 상대 경로
    root_path = Path(__file__).parent.parent.parent
    db_path = root_path / 'data' / 'database' / 'animal_data.db'
    
    # 경로가 없으면 생성
    os.makedirs(db_path.parent, exist_ok=True)
    
    # DB 연결
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 동물 정보 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS animals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT NOT NULL,
        name_ko TEXT,
        description TEXT,
        habitat TEXT,
        diet TEXT,
        lifespan TEXT,
        conservation_status TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 동물 이름 번역 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS animal_translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_ko TEXT NOT NULL,
        name_en TEXT NOT NULL,
        UNIQUE(name_ko, name_en)
    )
    ''')
    
    conn.commit()
    logger.info("Database tables created or already exist")
    
    return conn, cursor

# 이름을 URL용 슬러그로 변환
def to_url_slug(name):
    """
    이름을 URL 슬러그로 변환
    
    Args:
        name (str): 변환할 이름
        
    Returns:
        str: URL 슬러그
    """
    name = name.lower()
    name = re.sub(r"[''\",\.]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name

def save_animal_to_db(conn, cursor, en_name, ko_name, status_code):
    """
    동물 정보를 데이터베이스에 저장
    
    Args:
        conn: SQLite 연결 객체
        cursor: SQLite 커서 객체
        en_name (str): 영어 동물 이름
        ko_name (str): 한글 동물 이름
        status_code (str): 보전 상태 코드
        
    Returns:
        bool: 저장 성공 여부
    """
    if not en_name:
        return False
        
    try:
        # 이미 존재하는지 확인
        cursor.execute(
            "SELECT id FROM animals WHERE name_en = ?", 
            (en_name,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # 기존 데이터 업데이트
            cursor.execute('''
            UPDATE animals 
            SET name_ko = ?, conservation_status = ?
            WHERE name_en = ?
            ''', (ko_name, status_code.upper(), en_name))
            logger.info(f"Updated information for {en_name}")
        else:
            # 새 데이터 추가
            cursor.execute('''
            INSERT INTO animals (name_en, name_ko, conservation_status)
            VALUES (?, ?, ?)
            ''', (en_name, ko_name, status_code.upper()))
            logger.info(f"Added new animal: {en_name}")
        
        # 번역 정보 저장 (한글 이름이 있는 경우)
        if ko_name and not ko_name.startswith("[번역 없음]"):
            cursor.execute('''
            INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
            VALUES (?, ?)
            ''', (ko_name, en_name))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Database error for {en_name}: {str(e)}")
        conn.rollback()
        return False

def run_crawler(max_count=40):
    """
    IUCN 동물 크롤러 실행
    
    Args:
        max_count (int): 각 상태별 최대 동물 수 (기본값: 40)
    """
    conn, cursor = setup_database()
    
    # Chrome 옵션 설정
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    
    try:
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
                logger.info(f"[{code.upper()}] 동물 수: {animal_count}마리")
            except Exception as e:
                logger.error(f"[{code.upper()}] 동물 수를 가져오는데 실패했습니다. 예외: {str(e)}")
                animal_count = 0  # 예외가 발생하면 0으로 설정하여 계속 진행
            
            # 동물 수가 현재 저장된 수와 동일하거나 max_count 이상이면 해당 카테고리 스킵
            if animal_count == current_animal_count or current_animal_count >= max_count:
                logger.info(f"[{code.upper()}] 이미 {current_animal_count}개의 동물이 저장되어 있어 해당 카테고리를 스킵합니다.")
                continue
            
            logger.info(f"[{code.upper()}] 데이터 수집 시작")
            
            # 동물 이름 수집 시작
            en_names = []
            
            while True:
                # 동물 이름 추출 (class="f-h2")
                animal_elements = driver.find_elements(By.CLASS_NAME, "f-h2")
                new_animal_names = [el.text.strip() for el in animal_elements if el.text.strip()]
                
                if new_animal_names:
                    logger.info(f"[{code.upper()}] 수집된 동물 이름 {len(new_animal_names)}개")
                else:
                    logger.warning(f"[{code.upper()}] 동물 이름이 수집되지 않았습니다. 페이지를 확인해주세요.")
                
                # 새로운 동물 이름 중 중복되지 않은 이름만 추가
                for name in new_animal_names:
                    if len(en_names) < max_count:
                        if name.strip() not in en_names:  # 이름 앞뒤 공백도 제거하고 비교
                            en_names.append(name.strip())  # 추가 시 공백을 제거하고 저장
                    else:
                        logger.info(f"[{code.upper()}] {max_count}개 이름 수집 완료, 카테고리 스킵")
                        break  # max_count 이름이 수집되었으면 바로 해당 카테고리를 건너뜀
                
                # max_count가 다 채워지면 더 이상 동물 이름을 추가하지 않음
                if len(en_names) >= max_count:
                    logger.info(f"[{code.upper()}] {max_count}개 이름 수집 완료, 다음 등급으로 넘어갑니다.")
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
                    logger.debug("더 보기 버튼 클릭됨")
                    time.sleep(3)
                except Exception as e:
                    logger.debug("모든 동물 데이터를 로드했거나 버튼이 없습니다.")
                    break
            
            # 한글 이름 수집
            animals_data = []
            for en_name in en_names[:max_count]:
                url_slug = to_url_slug(en_name)
                driver.get(f"https://animalia.bio/ko/{url_slug}")
                
                try:
                    ko_name_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "a-h1"))
                    )
                    ko_name = ko_name_element.text.strip()
                    
                    # 한글 이름이 없으면 영어 이름을 사용
                    if not ko_name or ko_name == en_name:
                        ko_name = f"[번역 없음] {en_name}"
                except Exception as e:
                    logger.warning(f"Could not find Korean name for {en_name}: {str(e)}")
                    ko_name = f"[번역 없음] {en_name}"
                
                # 데이터베이스에 저장
                save_animal_to_db(conn, cursor, en_name, ko_name, code)
                
                # 파일에도 저장
                animals_data.append(f"{en_name} / {ko_name}")
                logger.info(f"[{code.upper()}] {en_name} / {ko_name}")
                
                # 잠시 대기 (웹사이트 부하 방지)
                time.sleep(1)
            
            # 파일에 저장
            with open(file_path, "w", encoding="utf-8") as f:
                for data in animals_data:
                    f.write(data + "\n")
            
            logger.info(f"[{code.upper()}] 동물 수집 완료: {len(animals_data)}마리 저장됨\n")
    
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
    
    finally:
        # 리소스 정리
        driver.quit()
        conn.close()
        logger.info("크롤링 작업 완료 및 리소스 정리")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IUCN 동물 정보 크롤러")
    parser.add_argument("--count", type=int, default=40, help="각 상태별 최대 동물 수 (기본값: 40)")
    args = parser.parse_args()
    
    run_crawler(max_count=args.count)