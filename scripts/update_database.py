# scripts/update_database.py
# 기존 크롤링 스크립트를 통합하여 데이터베이스 업데이트

import os
import sys
import sqlite3
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import argparse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("animal_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AnimalCrawler")

# 프로젝트 루트 경로 설정
ROOT_PATH = Path(__file__).parent.parent
sys.path.append(str(ROOT_PATH))

# DB 파일 경로
DB_PATH = ROOT_PATH / "data" / "database" / "animal_data.db"

# animalia.bio 기본 URL
BASE_URL = "https://animalia.bio"

# IUCN 보전 상태 코드 및 경로
CONSERVATION_STATUSES = {
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

def setup_database():
    """
    데이터베이스 설정 및 테이블 생성
    
    Returns:
        tuple: (연결 객체, 커서 객체)
    """
    # DB 경로의 디렉토리가 없으면 생성
    os.makedirs(DB_PATH.parent, exist_ok=True)
    
    # DB 연결
    conn = sqlite3.connect(str(DB_PATH))
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
    logger.info("Database setup completed")
    
    return conn, cursor

def get_webdriver():
    """
    Selenium 웹드라이버 설정
    
    Returns:
        webdriver: 설정된 Chrome 웹드라이버
    """
    options = Options()
    options.add_argument("--headless=new")  # 헤드리스 모드 (UI 없음)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise

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

def scrape_animal_list(driver, status_code, max_count=40):
    """
    특정 보전 상태에 해당하는 동물 목록 스크래핑
    
    Args:
        driver (webdriver): Selenium 웹드라이버
        status_code (str): 보전 상태 코드 (예: 'lc', 'en')
        max_count (int): 최대 수집 개수 (기본값: 40)
        
    Returns:
        list: 동물 이름 목록 [(영어 이름, 한글 이름)]
    """
    status_path = CONSERVATION_STATUSES.get(status_code, "")
    if not status_path:
        logger.error(f"Invalid conservation status code: {status_code}")
        return []
    
    logger.info(f"Scraping animals with conservation status: {status_code.upper()}")
    
    # 페이지 로드
    url = f"{BASE_URL}/{status_path}"
    driver.get(url)
    time.sleep(3)
    
    # 동물 이름 수집
    animal_names = []
    en_names = []
    
    while len(en_names) < max_count:
        # 동물 이름 요소 찾기
        animal_elements = driver.find_elements(By.CLASS_NAME, "f-h2")
        new_names = [el.text.strip() for el in animal_elements if el.text.strip()]
        
        # 새로운 이름 중 중복되지 않은 것만 추가
        for name in new_names:
            if name.lower() not in [n.lower() for n in en_names] and len(en_names) < max_count:
                en_names.append(name)
        
        # 최대 개수에 도달하면 종료
        if len(en_names) >= max_count:
            break
            
        # 페이지 아래로 스크롤
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(2)
        
        # "더 보기" 버튼 클릭 시도
        try:
            load_more = driver.find_element(By.CLASS_NAME, "load-more")
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
            time.sleep(1)
            load_more.click()
            logger.debug("Clicked 'Load more' button")
            time.sleep(3)
        except Exception as e:
            logger.debug("No more content to load or button not found")
            break
    
    logger.info(f"Collected {len(en_names)} English animal names")
    
    # 한글 이름 수집
    for en_name in en_names[:max_count]:
        url_slug = to_url_slug(en_name)
        
        try:
            driver.get(f"{BASE_URL}/ko/{url_slug}")
            time.sleep(2)
            
            try:
                # 한글 이름 추출 시도
                ko_name_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "a-h1"))
                )
                ko_name = ko_name_element.text.strip()
                
                # 한글 이름이 없으면 영어 이름 사용
                if not ko_name or ko_name == en_name:
                    ko_name = f"[번역 없음] {en_name}"
                    
                animal_names.append((en_name, ko_name))
                logger.debug(f"Found animal: {en_name} / {ko_name}")
                
            except Exception as e:
                logger.warning(f"Could not find Korean name for {en_name}: {str(e)}")
                animal_names.append((en_name, f"[번역 없음] {en_name}"))
                
        except Exception as e:
            logger.error(f"Error accessing page for {en_name}: {str(e)}")
            animal_names.append((en_name, f"[번역 없음] {en_name}"))
    
    logger.info(f"Collected {len(animal_names)} animal name pairs with conservation status {status_code.upper()}")
    return animal_names

def scrape_animal_details(driver, en_name, ko_name):
    """
    개별 동물의 상세 정보 스크래핑
    
    Args:
        driver (webdriver): Selenium 웹드라이버
        en_name (str): 영어 동물 이름
        ko_name (str): 한글 동물 이름
        
    Returns:
        dict: 동물 상세 정보
    """
    url_slug = to_url_slug(en_name)
    
    # 기본 정보 초기화
    animal_info = {
        "name_en": en_name,
        "name_ko": ko_name.replace("[번역 없음] ", ""),
        "description": "",
        "habitat": "",
        "diet": "",
        "lifespan": "",
        "conservation_status": ""
    }
    
    try:
        # 한글 페이지 로드 시도
        driver.get(f"{BASE_URL}/ko/{url_slug}")
        time.sleep(3)
        
        # 설명 추출 시도
        try:
            description_element = driver.find_element(By.CLASS_NAME, "animal-description")
            animal_info["description"] = description_element.text.strip()
        except Exception as e:
            logger.warning(f"Could not find description for {en_name}: {str(e)}")
        
        # 특성 정보 추출 시도 (서식지, 식성, 수명 등)
        try:
            characteristics = driver.find_elements(By.CLASS_NAME, "characteristics-item")
            for item in characteristics:
                try:
                    title = item.find_element(By.CLASS_NAME, "title").text.strip().lower()
                    value = item.find_element(By.CLASS_NAME, "value").text.strip()
                    
                    if "habitat" in title or "서식지" in title:
                        animal_info["habitat"] = value
                    elif "diet" in title or "식성" in title:
                        animal_info["diet"] = value
                    elif "lifespan" in title or "수명" in title:
                        animal_info["lifespan"] = value
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Could not find characteristics for {en_name}: {str(e)}")
        
        # 보전 상태 추출 시도
        try:
            status_element = driver.find_element(By.CLASS_NAME, "conservation-status")
            status_text = status_element.text.strip()
            
            # 정규식으로 상태 코드 추출 (예: "멸종 위기 (EN)" -> "EN")
            status_match = re.search(r'\(([A-Z]{2})\)', status_text)
            if status_match:
                animal_info["conservation_status"] = status_match.group(1)
        except Exception as e:
            logger.warning(f"Could not find conservation status for {en_name}: {str(e)}")
            
        logger.info(f"Successfully scraped details for {en_name}")
        return animal_info
        
    except Exception as e:
        logger.error(f"Error scraping details for {en_name}: {str(e)}")
        return animal_info

def save_to_database(conn, cursor, animal_info):
    """
    동물 정보를 데이터베이스에 저장
    
    Args:
        conn: SQLite 연결 객체
        cursor: SQLite 커서 객체
        animal_info (dict): 저장할 동물 정보
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 이미 존재하는지 확인
        cursor.execute(
            "SELECT id FROM animals WHERE name_en = ?", 
            (animal_info["name_en"],)
        )
        existing = cursor.fetchone()
        
        if existing:
            # 기존 데이터 업데이트
            cursor.execute('''
            UPDATE animals 
            SET name_ko = ?, description = ?, habitat = ?, diet = ?, lifespan = ?, conservation_status = ?
            WHERE name_en = ?
            ''', (
                animal_info["name_ko"],
                animal_info["description"],
                animal_info["habitat"],
                animal_info["diet"],
                animal_info["lifespan"],
                animal_info["conservation_status"],
                animal_info["name_en"]
            ))
            logger.info(f"Updated information for {animal_info['name_en']}")
        else:
            # 새 데이터 추가
            cursor.execute('''
            INSERT INTO animals (name_en, name_ko, description, habitat, diet, lifespan, conservation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                animal_info["name_en"],
                animal_info["name_ko"],
                animal_info["description"],
                animal_info["habitat"],
                animal_info["diet"],
                animal_info["lifespan"],
                animal_info["conservation_status"]
            ))
            logger.info(f"Added new animal: {animal_info['name_en']}")
        
        # 번역 정보 저장 (한글 이름이 있는 경우)
        if animal_info["name_ko"] and not animal_info["name_ko"].startswith("[번역 없음]"):
            cursor.execute('''
            INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
            VALUES (?, ?)
            ''', (animal_info["name_ko"], animal_info["name_en"]))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Database error for {animal_info['name_en']}: {str(e)}")
        conn.rollback()
        return False

def main():
    """
    메인 실행 함수
    """
    parser = argparse.ArgumentParser(description="동물 정보 크롤링 및 데이터베이스 업데이트")
    parser.add_argument(
        "--status", 
        type=str, 
        choices=list(CONSERVATION_STATUSES.keys()), 
        help="특정 보전 상태만 크롤링 (예: lc, en)"
    )
    parser.add_argument(
        "--count", 
        type=int, 
        default=40, 
        help="각 상태별 최대 동물 수 (기본값: 40)"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="데이터베이스 초기화 후 시작"
    )
    
    args = parser.parse_args()
    
    # 데이터베이스 설정
    conn, cursor = setup_database()
    
    # 데이터베이스 초기화
    if args.reset:
        logger.warning("Resetting database tables")
        cursor.execute("DROP TABLE IF EXISTS animals")
        cursor.execute("DROP TABLE IF EXISTS animal_translations")
        conn.commit()
        conn, cursor = setup_database()
    
    # 크롤링할 상태 목록
    statuses = [args.status] if args.status else CONSERVATION_STATUSES.keys()
    
    try:
        # 웹드라이버 초기화
        driver = get_webdriver()
        
        # 각 상태별 동물 크롤링
        for status in statuses:
            # 동물 목록 수집
            animal_names = scrape_animal_list(driver, status, args.count)
            
            # 각 동물의 상세 정보 수집 및 저장
            for en_name, ko_name in animal_names:
                animal_info = scrape_animal_details(driver, en_name, ko_name)
                
                # 상태 코드가 없으면 현재 루프의 상태 코드 사용
                if not animal_info["conservation_status"]:
                    animal_info["conservation_status"] = status.upper()
                
                # 데이터베이스에 저장
                save_to_database(conn, cursor, animal_info)
            
            logger.info(f"Completed crawling for status: {status.upper()}")
        
        logger.info("Crawling process completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred in the main process: {str(e)}")
    finally:
        # 리소스 정리
        if 'driver' in locals():
            driver.quit()
        conn.close()
        logger.info("Resources cleaned up")

if __name__ == "__main__":
    main()