# 데이터베이스 수정 및 확인 스크립트
# utils/fix_database.py

import sqlite3
from pathlib import Path
import os

# 프로젝트 루트 경로
ROOT_PATH = Path(__file__).parent.parent
DB_PATH = ROOT_PATH / 'data' / 'database' / 'animal_data.db'

def check_database():
    """현재 데이터베이스 상태 확인"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 동물 정보 테이블 확인
    cursor.execute("SELECT COUNT(*) FROM animals")
    count = cursor.fetchone()[0]
    print(f"총 동물 수: {count}")
    
    # deer 확인
    cursor.execute("SELECT * FROM animals WHERE name_en LIKE '%deer%'")
    deer_results = cursor.fetchall()
    print("\n사슴 관련 데이터:")
    for row in deer_results:
        print(f"ID: {row[0]}, EN: {row[1]}, KO: {row[2]}")
    
    # 번역 테이블 확인
    cursor.execute("SELECT * FROM animal_translations WHERE name_en LIKE '%deer%'")
    translation_results = cursor.fetchall()
    print("\n사슴 번역 정보:")
    for row in translation_results:
        print(f"ID: {row[0]}, KO: {row[1]}, EN: {row[2]}")
    
    conn.close()

def add_deer_translation():
    """사슴 번역 추가"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # animals 테이블에 사슴 추가 (없으면)
    cursor.execute('''
    INSERT OR IGNORE INTO animals (name_en, name_ko, description)
    VALUES (?, ?, ?)
    ''', ("deer", "사슴", "사슴은 우아하고 민첩한 초식동물입니다. 아름다운 뿔을 가진 종도 많습니다."))
    
    # 번역 테이블에 추가
    cursor.execute('''
    INSERT OR IGNORE INTO animal_translations (name_ko, name_en)
    VALUES (?, ?)
    ''', ("사슴", "deer"))
    
    conn.commit()
    print("\n사슴 번역 데이터 추가 완료")
    
    # 확인
    cursor.execute("SELECT * FROM animals WHERE name_en = 'deer'")
    result = cursor.fetchone()
    if result:
        print(f"등록된 데이터: {result}")
    
    conn.close()

def fix_database():
    """데이터베이스 문제 수정"""
    print("데이터베이스 상태 확인...")
    check_database()
    
    print("\n사슴 번역 데이터 추가 중...")
    add_deer_translation()
    
    print("\n수정 후 데이터베이스 상태 확인...")
    check_database()

if __name__ == "__main__":
    fix_database()
    