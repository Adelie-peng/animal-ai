# 🦁Zoo🐻Buddy🐨 - 동물 이미지 분석 챗봇

ZooBuddy는 사용자가 업로드한 동물 이미지를 분석하여 해당 동물의 정보를 제공하는 웹 애플리케이션입니다. MobileSAM을 사용한 세그멘테이션과 CLIP을 사용한 분류, 그리고 Gemini AI를 활용한 대화형 답변을 통해 사용자에게 풍부한 동물 정보를 제공합니다.

## 기능

- 동물 이미지 업로드 및 분석
- 세그멘테이션을 통한 동물 영역 추출
- 딥러닝 모델을 통한 동물 종 분류
- 동물에 대한 정보 조회 및 친근한 설명 생성
- 한글 동물 이름 입력을 통한 정보 검색

## 기술 스택

- **백엔드**: FastAPI, Python
- **프론트엔드**: HTML, CSS, JavaScript
- **AI 모델**:
  - MobileSAM (세그멘테이션)
  - CLIP (이미지 분류)
  - Gemini AI (텍스트 생성)
- **데이터 수집**: Selenium 웹 크롤링

## 프로젝트 구조

```
ZooBuddy/
├── app/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analyze.py
│   │   ├── predict.py
│   │   └── upload.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── animal_data.py
│   │   ├── animal_info_service.py
│   │   ├── chat_service.py
│   │   ├── classifier_service.py
│   │   ├── db_service.py
│   │   ├── model.py
│   │   ├── response_service.py
│   │   └── sam_service.py
│   ├── templates/
│   │   ├── index.html
│   │   └── result.html
│   ├── __init__.py
│   └── app.py
├── data/
│   ├── animals/
│   └── database/
│       └── animal_data.db
├── external/
│   └── MobileSAM/
│       └── weights/
│           └── mobile_sam.pt
├── scripts/
│   ├── crawling/
│   │   ├── animal_crawler.py
│   │   ├── iucn_crawler.py
│   │   └── utils.py
│   └── update_database.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── README.md
```

## 설치 및 실행 방법

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
conda create -n animal-ai python=3.10
conda activate animal-ai

# 필요한 패키지 설치
pip install -r requirements.txt

# MobileSAM 설치
git clone https://github.com/ChaoningZhang/MobileSAM.git external/MobileSAM
pip install -e external/MobileSAM
```

### 2. 데이터베이스 구축

```bash
# 동물 정보 크롤링 및 데이터베이스 구축
python scripts/update_database.py --count 20 --status lc
```

옵션 설명:
- `--count`: 각 보전 상태별 크롤링할 동물 수 (기본값: 40)
- `--status`: 특정 보전 상태만 크롤링 (lc, en, vu 등)
- `--reset`: 데이터베이스 초기화 후 시작

### 3. 애플리케이션 실행

```bash
# 백엔드 서버 실행
uvicorn app.app:app --reload

# 브라우저에서 접속
# http://localhost:8000
```

## 작동 과정

1. 사용자가 동물 이미지를 업로드합니다.
2. 이미지가 백엔드 서버로 전송됩니다.
3. MobileSAM 모델이 이미지에서 동물을 세그멘테이션합니다.
4. CLIP 모델이 세그멘테이션된 이미지를 분석하여 동물을 분류합니다.
5. 분류된 동물 정보를 데이터베이스에서 조회합니다.
6. Gemini AI가 동물 정보를 기반으로 친근한 설명을 생성합니다.
7. 결과가 사용자에게 표시됩니다.

## API 엔드포인트

- `POST /api/analyze/`: 동물 이미지 분석 (세그멘테이션, 분류, 정보 조회)
- `POST /api/predict`: 동물 이미지 세그멘테이션만 수행
- `POST /api/upload`: 이미지 업로드 및 간단한 정보 조회
- `GET /api/text/{animal_kr}`: 한글 동물 이름으로 정보 조회

## 팀원 및 역할

- adelie: 백엔드 개발, AI 모델 통합 (MobileSAM, CLIP), Gemini AI 연동
- ggsoxman: 프론트엔드 개발, 데이터 수집 및 크롤링, 데이터베이스 구축

## 문제 해결

문제 발생 시:

1. 로그 확인: `animal_crawler.log`, FastAPI 서버 로그
2. 데이터베이스 확인: `data/database/animal_data.db`
3. 모델 가중치 확인: `external/MobileSAM/weights/mobile_sam.pt`

## 라이센스

MIT License