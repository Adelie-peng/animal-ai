from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class TempStorageService:
    _instance = None  # 싱글톤 패턴을 위한 인스턴스 저장 변수
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TempStorageService, cls).__new__(cls)
            cls._instance._storage = {}
            cls._instance.expiry_minutes = 30  # 기본 만료 시간
        return cls._instance
    
    def __init__(self, expiry_minutes: int = 30):
        # 이미 초기화된 인스턴스는 재초기화하지 않음
        if hasattr(self, '_storage'):
            return
        self._storage = {}
        self.expiry_minutes = expiry_minutes
    
    def store(self, result_id: str, data: Dict[str, Any]) -> None:
        """결과 데이터를 임시 저장소에 저장"""
        self._storage[result_id] = {
            'data': data,
            'expires_at': datetime.now() + timedelta(minutes=self.expiry_minutes)
        }
        
    def get(self, result_id: str) -> Optional[Dict[str, Any]]:
        """ID로 결과 데이터 조회"""
        result = self._storage.get(result_id)
        
        # 데이터가 없거나 만료된 경우
        if not result or datetime.now() > result['expires_at']:
            if result:
                # 만료된 데이터 삭제
                del self._storage[result_id]
            return None
            
        return result['data']
    
    def cleanup(self) -> None:
        """만료된 데이터 정리"""
        now = datetime.now()
        expired_keys = [
            k for k, v in self._storage.items() 
            if now > v['expires_at']
        ]
        
        for key in expired_keys:
            del self._storage[key]
            