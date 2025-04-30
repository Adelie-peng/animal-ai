from typing import Dict, Optional
import requests
from urllib3.util import Retry  # 변경된 import 문
from bs4 import BeautifulSoup
from urllib.parse import quote
import logging
from functools import lru_cache
from dataclasses import dataclass
from requests.adapters import HTTPAdapter

# 로거 설정
logger = logging.getLogger(__name__)

@dataclass
class ScrapingError(Exception):
    """스크래핑 과정에서 발생하는 예외를 처리하는 클래스"""
    message: str
    details: Optional[Dict] = None

class AnimalScraper:
    """동물 정보 스크래핑 클래스"""
    
    def __init__(self):
        """스크래퍼 초기화 및 한영 사전 설정"""
        self.ko_en_dict: Dict[str, str] = {
            "사자": "lion",
            "호랑이": "tiger",
            "코끼리": "elephant",
            "여우": "fox",
            "늑대": "wolf",
            "고양이": "cat",
            "개": "dog",
            "팬더": "panda",
            "기린": "giraffe",
            "원숭이": "monkey",
        }
        
        # HTTP 세션 설정
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retry))
        logger.info("AnimalScraper initialized successfully")

    def korean_to_english(self, animal_kr: str) -> str:
        """
        한글 동물 이름을 영어로 변환
        
        Args:
            animal_kr (str): 한글 동물 이름
            
        Returns:
            str: 영어 동물 이름
        """
        try:
            animal_kr = animal_kr.strip()
            translated = self.ko_en_dict.get(animal_kr)
            
            if translated:
                logger.debug(f"Translated {animal_kr} to {translated}")
                return translated
            
            logger.warning(f"No translation found for: {animal_kr}")
            return animal_kr
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return animal_kr

    @lru_cache(maxsize=100)
    def scrape_animal_info(self, animal_en: str) -> Dict[str, str]:
        """
        animalia.bio에서 동물 정보 스크래핑
        
        Args:
            animal_en (str): 영어 동물 이름
            
        Returns:
            Dict[str, str]: {
                "description": str,  # 동물 설명
                "status": str        # 스크래핑 상태
            }
            
        Raises:
            ScrapingError: 스크래핑 실패 시
        """
        try:
            url = f"https://animalia.bio/ko/{quote(animal_en)}"
            logger.info(f"Scraping info for {animal_en} from {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            desc = soup.find("div", {"class": "field-body"})

            if desc:
                info = desc.text.strip()
                logger.debug(f"Successfully scraped info for {animal_en}")
                return {
                    "description": info,
                    "status": "success"
                }
            
            logger.warning(f"No information found for {animal_en}")
            return {
                "description": "동물 정보를 찾을 수 없습니다.",
                "status": "not_found"
            }
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {animal_en}: {str(e)}")
            return {
                "description": f"네트워크 오류: {str(e)}",
                "status": "error"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error while scraping {animal_en}: {str(e)}")
            raise ScrapingError(
                message="스크래핑 실패",
                details={"animal": animal_en, "error": str(e)}
            )

    def __del__(self):
        """리소스 정리"""
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Failed to close session: {str(e)}")
