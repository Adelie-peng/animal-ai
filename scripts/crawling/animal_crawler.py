# scripts/crawling/animal_crawler.py 개선안
import os
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from pathlib import Path

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

class AnimaliaCrawler:
    """Animalia.bio 웹사이트에서 동물 정보를 크롤링하는 클래스"""
    
    def __init__(self, db_path=None):
        """
        크롤러 초기화
        
        Args:
            db_path (str, optional): 데이터베이스 파일 경로. None이면 기본 경로 사용.
        """
        # WebDriver 옵션 설정
        self.options = self._get_headless_options()
        self.driver = None
        
        # 데이터베이스 경로 설정
        if db_path is None:
            # 프로젝트 루트 기준 상대 경로
            root_path = Path(__file__).parent.parent.parent
            self.db_path = root_path / 'data' / 'database' / 'animal_data.db'
            # 경로가 없으면 생성
            os.makedirs(self.db_path.parent, exist_ok=True)
        else:
            self.db_path = Path(db_path)
        
        # 데이터베이스 연결 및 테이블 생성
        self.conn = self._setup_database()
        
        logger.info("AnimaliaCrawler initialized")
    
    def _get_headless_options(self):
        """
        헤드리스 모드 WebDriver 옵션 설정
        
        Returns:
            Options: 설정된 ChromeOptions 객체
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return options
    
    def _setup_database(self):
        """
        데이터베이스 연결 및 테이블 생성
        
        Returns:
            Connection: SQLite 연결 객체
        """
        conn = sqlite3.connect(str(self.db_path))
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
        
        return conn
    
    def start_driver(self):
        """Selenium WebDriver 시작"""
        if self.driver is None:
            try:
                self.driver = webdriver.Chrome(options=self.options)
                logger.info("WebDriver started")
            except Exception as e:
                logger.error(f"Failed to start WebDriver: {str(e)}")
                raise
    
    def crawl(self, animal_name):
        """
        동물 이름으로 정보 크롤링
        
        Args:
            animal_name (str): 크롤링할 동물 이름
            
        Returns:
            dict: 크롤링된 동물 정보
        """
        self.start_driver()
        
        try:
            # 영어 페이지 접속
            self.driver.get(f"https://animalia.bio/{animal_name.lower().replace(' ', '-')}")
            time.sleep(2)
            
            # 기본 정보 초기화
            animal_info = {
                "name_en": animal_name,
                "name_ko": "",
                "description": "",
                "habitat": "",
                "diet": "",
                "conservation_status": ""
            }
            
            # 설명 추출
            try:
                description_element = self.driver.find_element(By.CLASS_NAME, "animal-description")
                animal_info["description"] = description_element.text.strip()
            except Exception as e:
                logger.warning(f"Could not find description for {animal_name}: {str(e)}")
            
            # IUCN 보전 상태 추출
            try:
                status_element = self.driver.find_element(By.CLASS_NAME, "conservation-status")
                status_text = status_element.text.strip()
                # "Vulnerable (VU)" -> "VU"
                if "(" in status_text and ")" in status_text:
                    animal_info["conservation_status"] = status_text.split("(")[1].split(")")[0]
            except Exception as e:
                logger.warning(f"Could not find conservation status for {animal_name}: {str(e)}")
            
            # 한글 이름 조회를 위해 한글 페이지 접속
            try:
                self.driver.get(f"https://animalia.bio/ko/{animal_name.lower().replace(' ', '-')}")
                time.sleep(2)
                
                ko_name_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "a-h1"))
                )
                animal_info["name_ko"] = ko_name_element.text.strip()
            except Exception as e:
                logger.warning(f"Could not find Korean name for {animal_name}: {str(e)}")
            
            # 데이터베이스에 저장
            self.save_to_db(animal_info)
            
            logger.info(f"Successfully crawled information for {animal_name}")
            return animal_info
            
        except Exception as e:
            logger.error(f"Error crawling {animal_name}: {str(e)}")
            return None
    
    def save_to_db(self, animal_info):
        """
        동물 정보를 데이터베이스에 저장
        
        Args:
            animal_info (dict): 저장할 동물 정보
            
        Returns:
            bool: 저장 성공 여부
        """
        if not animal_info or not animal_info["name_en"]:
            return False
            
        try:
            cursor = self.conn.cursor()
            
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
                SET name_ko = ?, description = ?, habitat = ?, diet = ?, conservation_status = ?
                WHERE name_en = ?
                ''', (
                    animal_info.get("name_ko", ""),
                    animal_info.get("description", ""),
                    animal_info.get("habitat", ""),
                    animal_info.get("diet", ""),
                    animal_info.get("conservation_status", ""),
                    animal_info["name_en"]
                ))
                logger.info(f"Updated information for {animal_info['name_en']}")
            else:
                # 새 데이터 추가
                cursor.execute('''
                INSERT INTO animals (name_en, name_ko, description, habitat, diet, conservation_status)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    animal_info["name_en"],
                    animal_info.get("name_ko", ""),
                    animal_info.get("description", ""),
                    animal_info.get("habitat", ""),
                    animal_info.get("diet", ""),
                    animal_info.get("conservation_status", "")
                ))
                logger.info(f"Added new animal: {animal_info['name_en']}")
            
            # 번역 정보 저장 (한글 이름이 있는 경우)
            if animal_info.get("name_ko"):
                cursor.execute('''
                INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
                VALUES (?, ?)
                ''', (animal_info["name_ko"], animal_info["name_en"]))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database error for {animal_info['name_en']}: {str(e)}")
            self.conn.rollback()
            return False
    
    def close(self):
        """리소스 정리"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver closed")
            
            if self.conn:
                self.conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")
    
    def __del__(self):
        """소멸자"""
        self.close()

# 예시 사용법
if __name__ == "__main__":
    crawler = AnimaliaCrawler()
    
    try:
        # 동물 목록
        animals = ["lion", "tiger", "elephant", "giraffe", "panda"]
        
        for animal in animals:
            info = crawler.crawl(animal)
            if info:
                print(f"Crawled: {info['name_en']} / {info['name_ko']}")
                print(f"Conservation status: {info['conservation_status']}")
                print("-" * 50)
    
    finally:
        crawler.close()