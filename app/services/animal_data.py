# app/services/animal_data.py
# 기존 scripts/crawling 모듈의 기능을 통합한 모듈

import os
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# 로거 설정
logger = logging.getLogger(__name__)

class AnimalDataService:
    """
    scripts/crawling의 크롤링 모듈에서 수집한 동물 데이터를 제공하는 서비스
    """
    
    def __init__(self):
        """
        데이터베이스 연결 및 초기화
        """
        try:
            # 데이터베이스 파일 경로
            self.db_path = Path(__file__).parent.parent.parent / 'data' / 'database' / 'animal_data.db'
            
            # 데이터베이스 디렉토리가 없으면 생성
            os.makedirs(self.db_path.parent, exist_ok=True)
            
            # 데이터베이스 연결
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()
            
            # 테이블이 없으면 생성
            self._create_tables_if_not_exist()
            
            # 샘플 데이터 추가 (실제 데이터베이스에 데이터가 없을 경우)
            if self._count_animals() == 0:
                self._insert_sample_data()
                
            logger.info("AnimalDataService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AnimalDataService: {str(e)}")
            raise
            
    def _create_tables_if_not_exist(self):
        """
        필요한 테이블 생성
        """
        try:
            # 동물 정보 테이블 생성
            self.cursor.execute('''
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
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS animal_translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ko TEXT NOT NULL,
                name_en TEXT NOT NULL,
                UNIQUE(name_ko, name_en)
            )
            ''')
            
            self.conn.commit()
            logger.debug("Database tables created or already exist")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def _count_animals(self) -> int:
        """
        동물 데이터 수 확인
        
        Returns:
            int: 동물 데이터 수
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM animals")
            return self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to count animals: {str(e)}")
            return 0
    
    def _insert_sample_data(self):
        """
        샘플 동물 데이터 추가 (실제 데이터가 없을 경우)
        """
        try:
            # 샘플 데이터
            sample_animals = [
                ("dog", "개", "개는 인간과 가장 오랫동안 함께한 반려동물입니다. 충성심이 강하고 다양한 품종이 있으며, 인간과의 깊은 유대감을 형성합니다.", "전 세계", "잡식성", "10-13년", "LC"),
                ("cat", "고양이", "고양이는 독립적인 성격을 가진 우아한 반려동물입니다. 사냥 본능이 강하고, 깨끗한 것을 좋아하며 자신만의 영역을 중요시합니다.", "전 세계", "육식성", "12-18년", "LC"),
                ("lion", "사자", "사자는 '동물의 왕'으로 불리는 대형 고양이과 동물입니다. 무리를 이루어 생활하며 수컷은 특유의 갈기를 가지고 있습니다.", "아프리카 초원", "육식성", "10-14년", "VU"),
                ("tiger", "호랑이", "호랑이는 고양이과에서 가장 큰 동물로, 강력한 근육과 특유의 줄무늬가 특징입니다. 단독 생활을 하며 영역을 중요시합니다.", "아시아", "육식성", "10-15년", "EN"),
                ("panda", "판다", "판다는 대나무를 주식으로 하는 곰과의 동물입니다. 흑백의 독특한 털 색깔과 귀여운 외모로 많은 사랑을 받고 있습니다.", "중국 산악지대", "초식성", "20년", "VU"),
            ]
            
            # 동물 정보 추가
            for animal in sample_animals:
                self.cursor.execute('''
                INSERT INTO animals (name_en, name_ko, description, habitat, diet, lifespan, conservation_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', animal)
                
                # 번역 정보 추가
                self.cursor.execute('''
                INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
                VALUES (?, ?)
                ''', (animal[1], animal[0]))
            
            self.conn.commit()
            logger.info(f"Added {len(sample_animals)} sample animals to the database")
            
        except Exception as e:
            logger.error(f"Failed to insert sample data: {str(e)}")
            self.conn.rollback()
    
    def get_animal_info(self, animal_name: str, lang: str = 'en') -> Optional[Dict[str, str]]:
        """
        동물 이름으로 정보 조회
        
        Args:
            animal_name (str): 동물 이름 (영어 또는 한글)
            lang (str): 검색 언어 ('en' 또는 'ko')
            
        Returns:
            Optional[Dict[str, str]]: 동물 정보 또는 None (정보가 없을 경우)
        """
        try:
            # 입력값 전처리
            animal_name = animal_name.lower().strip()
            
            # 'a', 'the' 등의 관사 제거
            if lang == 'en':
                animal_name = animal_name.replace("a ", "").replace("the ", "").strip()
            
            # 언어에 따른 쿼리 필드 설정
            name_field = "name_en" if lang == 'en' else "name_ko"
            
            # 동물 정보 조회
            self.cursor.execute(f'''
            SELECT name_en, name_ko, description, habitat, diet, lifespan, conservation_status
            FROM animals
            WHERE LOWER({name_field}) = ?
            ''', (animal_name,))
            
            result = self.cursor.fetchone()
            
            if not result:
                logger.warning(f"No animal information found for: {animal_name} (lang: {lang})")
                return None
                
            # 결과 딕셔너리 생성
            animal_info = {
                "name_en": result[0],
                "name_ko": result[1],
                "description": result[2],
                "habitat": result[3],
                "diet": result[4],
                "lifespan": result[5],
                "conservation_status": result[6]
            }
            
            logger.info(f"Retrieved information for animal: {animal_name}")
            return animal_info
            
        except Exception as e:
            logger.error(f"Error retrieving animal info: {str(e)}")
            return None
    
    def translate_animal_name(self, name: str, source_lang: str, target_lang: str) -> Optional[str]:
        """
        동물 이름 번역
        
        Args:
            name (str): 번역할 동물 이름
            source_lang (str): 원본 언어 ('ko' 또는 'en')
            target_lang (str): 대상 언어 ('ko' 또는 'en')
            
        Returns:
            Optional[str]: 번역된 이름 또는 None (번역 실패 시)
        """
        try:
            # 입력값 전처리
            name = name.lower().strip()
            
            # 동일 언어인 경우 그대로 반환
            if source_lang == target_lang:
                return name
                
            # 번역 방향에 따른 필드 설정
            source_field = "name_ko" if source_lang == "ko" else "name_en"
            target_field = "name_ko" if target_lang == "ko" else "name_en"
            
            # 먼저 번역 테이블에서 검색
            self.cursor.execute(f'''
            SELECT {target_field}
            FROM animal_translations
            WHERE LOWER({source_field}) = ?
            ''', (name,))
            
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
                
            # 번역 테이블에 없으면 동물 정보 테이블에서 검색
            self.cursor.execute(f'''
            SELECT {target_field}
            FROM animals
            WHERE LOWER({source_field}) = ?
            ''', (name,))
            
            result = self.cursor.fetchone()
            
            if result:
                # 번역 테이블에 추가
                source_val = name
                target_val = result[0]
                
                self.cursor.execute('''
                INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
                VALUES (?, ?)
                ''', (source_val if source_lang == "ko" else target_val, 
                      source_val if source_lang == "en" else target_val))
                
                self.conn.commit()
                return result[0]
                
            logger.warning(f"No translation found for: {name} ({source_lang} -> {target_lang})")
            return None
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return None
    
    def get_conservation_info(self, status_code: str) -> Dict[str, str]:
        """
        보전 상태 코드에 대한 상세 정보 제공
        
        Args:
            status_code (str): 보전 상태 코드 (예: 'LC', 'VU', 'EN', 'CR' 등)
            
        Returns:
            Dict[str, str]: 보전 상태 정보
        """
        # IUCN 보전 상태 정보
        conservation_info = {
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
        
        # 상태 코드 대문자로 변환
        status_code = status_code.upper() if status_code else "NE"
        
        # 기본값 반환 (코드가 일치하지 않을 경우)
        if status_code not in conservation_info:
            logger.warning(f"Unknown conservation status code: {status_code}")
            status_code = "NE"
            
        return conservation_info[status_code]
    
    def search_animals(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        동물 이름 또는 설명 검색
        
        Args:
            query (str): 검색어
            limit (int): 최대 결과 수
            
        Returns:
            List[Dict[str, str]]: 검색 결과 목록
        """
        try:
            # 검색어 형식 설정
            search_query = f"%{query.lower()}%"
            
            # 동물 정보 검색
            self.cursor.execute('''
            SELECT name_en, name_ko, description
            FROM animals
            WHERE LOWER(name_en) LIKE ? OR LOWER(name_ko) LIKE ? OR LOWER(description) LIKE ?
            LIMIT ?
            ''', (search_query, search_query, search_query, limit))
            
            results = self.cursor.fetchall()
            
            # 결과 변환
            animal_list = [
                {
                    "name_en": result[0],
                    "name_ko": result[1],
                    "description": result[2][:100] + "..." if len(result[2]) > 100 else result[2]
                }
                for result in results
            ]
            
            logger.info(f"Found {len(animal_list)} animals matching query: {query}")
            return animal_list
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def __del__(self):
        """
        리소스 정리
        """
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                logger.debug("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

# 전역 인스턴스 생성
try:
    animal_data_service = AnimalDataService()
    logger.info("Global AnimalDataService instance created successfully")
except Exception as e:
    logger.critical(f"Failed to create global AnimalDataService instance: {str(e)}")
    raise