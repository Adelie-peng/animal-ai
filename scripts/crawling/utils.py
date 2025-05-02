import os
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.keys import Keys
import re  # 정규식을 사용하여 숫자만 추출
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("animal_utils.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AnimalUtils")

# 데이터베이스 설정
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

def save_to_db(name, status, description="", habitat="", diet="", lifespan=""):
    """
    동물 정보를 데이터베이스에 저장
    
    Args:
        name (str or tuple): 동물 이름 (영어 이름 또는 (영어 이름, 한글 이름) 튜플)
        status (str): 보전 상태 코드
        description (str, optional): 동물 설명
        habitat (str, optional): 서식지
        diet (str, optional): 식습관
        lifespan (str, optional): 수명
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        conn, cursor = setup_database()
        
        # 이름 처리
        if isinstance(name, tuple):
            en_name, ko_name = name
        else:
            en_name = name
            ko_name = ""
        
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
            SET name_ko = ?, description = ?, habitat = ?, diet = ?, lifespan = ?, conservation_status = ?
            WHERE name_en = ?
            ''', (ko_name, description, habitat, diet, lifespan, status.upper(), en_name))
            logger.info(f"Updated information for {en_name}")
        else:
            # 새 데이터 추가
            cursor.execute('''
            INSERT INTO animals (name_en, name_ko, description, habitat, diet, lifespan, conservation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (en_name, ko_name, description, habitat, diet, lifespan, status.upper()))
            logger.info(f"Added new animal: {en_name}")
        
        # 번역 정보 저장 (한글 이름이 있는 경우)
        if ko_name:
            cursor.execute('''
            INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
            VALUES (?, ?)
            ''', (ko_name, en_name))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Database error for {name}: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False

def get_animal_info(name, lang='en'):
    """
    데이터베이스에서 동물 정보 조회
    
    Args:
        name (str): 동물 이름 (영어 또는 한글)
        lang (str): 이름 언어 ('en' 또는 'ko')
        
    Returns:
        dict: 동물 정보 또는 None (정보가 없을 경우)
    """
    try:
        conn, cursor = setup_database()
        
        # 언어에 따른 필드 선택
        field = "name_en" if lang == 'en' else "name_ko"
        
        # 정보 조회
        cursor.execute(f'''
        SELECT name_en, name_ko, description, habitat, diet, lifespan, conservation_status
        FROM animals
        WHERE {field} = ?
        ''', (name,))
        
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"No information found for: {name}")
            conn.close()
            return None
            
        # 결과 딕셔너리 변환
        animal_info = {
            "name_en": result[0],
            "name_ko": result[1],
            "description": result[2],
            "habitat": result[3],
            "diet": result[4],
            "lifespan": result[5],
            "conservation_status": result[6]
        }
        
        conn.close()
        return animal_info
        
    except Exception as e:
        logger.error(f"Error retrieving animal info: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def translate_animal_name(name, source_lang, target_lang):
    """
    동물 이름 번역 (데이터베이스 조회)
    
    Args:
        name (str): 번역할 동물 이름
        source_lang (str): 원본 언어 ('en' 또는 'ko')
        target_lang (str): 대상 언어 ('en' 또는 'ko')
        
    Returns:
        str: 번역된 이름 또는 None (번역 실패 시)
    """
    try:
        if source_lang == target_lang:
            return name
            
        conn, cursor = setup_database()
        
        # 원본 필드와 대상 필드 설정
        source_field = "name_ko" if source_lang == 'ko' else "name_en"
        target_field = "name_ko" if target_lang == 'ko' else "name_en"
        
        # 번역 조회
        cursor.execute(f'''
        SELECT {target_field}
        FROM animals
        WHERE {source_field} = ?
        ''', (name,))
        
        result = cursor.fetchone()
        
        if result and result[0]:
            conn.close()
            return result[0]
            
        # 번역 테이블에서 조회
        cursor.execute(f'''
        SELECT {target_field}
        FROM animal_translations
        WHERE {source_field} = ?
        ''', (name,))
        
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result and result[0] else None
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def get_conservation_status_info(status_code):
    """
    보전 상태 코드에 대한 상세 정보
    
    Args:
        status_code (str): 보전 상태 코드 (예: 'LC', 'EN')
        
    Returns:
        dict: 보전 상태 정보
    """
    status_info = {
        "EX": {
            "name": "Extinct (멸종)",
            "description": "이 종은 완전히 멸종되었습니다.",
            "color": "#000000"
        },
        "EW": {
            "name": "Extinct in the Wild (야생에서 멸종)",
            "description": "이 종은 야생에서는 멸종되었지만, 동물원이나 다른 보호 시설에서 생존하고 있습니다.",
            "color": "#542344"
        },
        "CR": {
            "name": "Critically Endangered (심각한 위기)",
            "description": "이 종은 극도로 높은 멸종 위험에 처해 있습니다.",
            "color": "#D9171A"
        },
        "EN": {
            "name": "Endangered (위기)",
            "description": "이 종은 멸종 위기에 처해 있습니다.",
            "color": "#E6752F"
        },
        "VU": {
            "name": "Vulnerable (취약)",
            "description": "이 종은 자연에서 멸종 위험이 높습니다.",
            "color": "#FFC14C"
        },
        "NT": {
            "name": "Near Threatened (준위협)",
            "description": "이 종은 현재 위협받고 있지는 않지만, 가까운 미래에 위협받을 가능성이 있습니다.",
            "color": "#0085FF"
        },
        "LC": {
            "name": "Least Concern (최소 관심)",
            "description": "이 종은 널리 분포하고 개체수가 많아 위협받지 않습니다.",
            "color": "#1FDB00"
        },
        "DD": {
            "name": "Data Deficient (정보 부족)",
            "description": "이 종에 대한 정보가 부족하여 위험 수준을 평가할 수 없습니다.",
            "color": "#CCCCCC"
        },
        "NE": {
            "name": "Not Evaluated (평가되지 않음)",
            "description": "이 종은 아직 IUCN 적색 목록 기준으로 평가되지 않았습니다.",
            "color": "#FFFFFF"
        }
    }
    
    status_code = status_code.upper() if status_code else "NE"
    
    return status_info.get(status_code, status_info["NE"])

def create_sqlite_database_from_files():
    """
    기존 텍스트 파일에서 SQLite 데이터베이스 생성
    각 보전 상태별 파일을 읽어 통합 데이터베이스 생성
    """
    try:
        conn, cursor = setup_database()
        
        # 프로젝트 루트 경로
        root_path = Path(__file__).parent.parent.parent
        
        # 업데이트된 경로: data/animals/{status}/animals.txt
        for code in ["ne", "dd", "lc", "nt", "vu", "en", "cr", "ew", "ex"]:
            # 새로운 경로 구조
            file_path = root_path / "data" / "animals" / code / "animals.txt"
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
                
            logger.info(f"Reading animal data from: {file_path}")
                
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 영어 / 한글 형식 파싱
                parts = line.split(" / ")
                if len(parts) == 2:
                    en_name, ko_name = parts
                else:
                    en_name = line
                    ko_name = ""
                
                # 데이터베이스에 저장
                save_to_db((en_name, ko_name), code)
                
            logger.info(f"Imported {len(lines)} animals from {file_path}")
            
        conn.close()
        logger.info("Database creation from files completed")
        
    except Exception as e:
        logger.error(f"Error creating database from files: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()

# 직접 실행 시 파일에서 데이터베이스 생성
if __name__ == "__main__":
    create_sqlite_database_from_files()