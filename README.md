# Animal-AI 🦁🐻🐨

"Animal-AI"는 동물 사진을 입력하면,
해당 동물에 대한 정보를 제공하고 대화를 이어갈 수 있는 AI 챗봇입니다.

## 주요 기능
- 사진 업로드를 통한 동물 종류 인식 (SAM + CLIP)
- 동물 관련 정보 제공 (Animalia.bio 기반 스크래핑)
- 친근하고 자연스러운 대화 지원 (LLM 기반)

## 기술 스택
- Python 3.10
- FastAPI
- MobileSAM (Segmentation)
- CLIP (Image Classification)
- Hugging Face LLM (Chatbot)
- BeautifulSoup4 (Web Scraping)

## 프로젝트 구조
project-root/
│
├── app/
│   ├── routers/
│   │   ├── predict.py
│   │   └── upload.py
│   │
│   ├── services/
│   │   ├── model.py
│   │   └── scraper.py
│
├── external/
│   └── MobileSAM/
│
├── requirements/
│   ├── conda-requirements.txt
│   └── pip-requirements.txt
│
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── commit_template.txt
│   └── CONTRIBUTING.md
│
├── .gitignore
├── main.py
└── README.md
