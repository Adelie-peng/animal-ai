# 데이터 수집 스크립트

## 동물 데이터 크롤러
- `crawling/animal_crawler.py`: animalia.bio에서 동물 정보 수집
- `crawling/iucn_crawler.py`: IUCN 보존 상태별 동물 목록 수집
- `crawling/utils.py`: 크롤링 유틸리티 함수

## 사용 방법
1. Chrome WebDriver 설치
2. 필요한 패키지 설치:
```bash
pip install selenium beautifulsoup4
```
3. 스크립트 실행:
```bash
python crawling/animal_crawler.py
```