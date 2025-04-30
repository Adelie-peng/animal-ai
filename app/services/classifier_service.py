import torch
import clip
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass

# 로거 설정
logger = logging.getLogger(__name__)

@dataclass
class ClassificationError(Exception):
    """분류 과정에서 발생하는 예외를 처리하는 클래스"""
    message: str
    details: Optional[Dict] = None

class AnimalClassifier:
    """CLIP 모델을 사용하여 동물을 분류하는 클래스"""
    
    def __init__(self):
        """CLIP 모델과 동물 클래스 초기화"""
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
            # CLIP 모델 로드
            self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
            self.model.eval()  # 추론 모드로 설정
            
            # 동물 클래스 정의
            self.ANIMAL_CLASSES: List[str] = [
                "a dog", "a cat", "a lion", "a tiger", "a bear",
                "a horse", "a panda", "a fox", "a rabbit", "a deer",
                "a wolf", "a monkey", "a elephant", "a giraffe", "a zebra"
            ]
            
            # 텍스트 임베딩 미리 계산 및 캐시
            self._cache_text_features()
            logger.info("AnimalClassifier initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AnimalClassifier: {str(e)}")
            raise ClassificationError("모델 초기화 실패")

    def _cache_text_features(self) -> None:
        """텍스트 특징을 미리 계산하여 캐시"""
        try:
            self.text_inputs = clip.tokenize(
                [f"a photo of {cls}" for cls in self.ANIMAL_CLASSES]
            ).to(self.device)
            
            with torch.no_grad():
                self.text_features = self.model.encode_text(self.text_inputs)
                
            logger.debug("Text features cached successfully")
            
        except Exception as e:
            logger.error(f"Text feature caching failed: {str(e)}")
            raise ClassificationError("텍스트 특징 캐시 실패")

    def crop_animal_region(self, image: Image.Image, mask: np.ndarray) -> Image.Image:
        """
        세그멘테이션 마스크를 이용해 동물 영역만 잘라냄
        
        Args:
            image (Image.Image): 원본 이미지
            mask (np.ndarray): 세그멘테이션 마스크
            
        Returns:
            Image.Image: 마스크가 적용된 이미지
            
        Raises:
            ClassificationError: 이미지 처리 실패 시
        """
        try:
            # 이미지와 마스크 크기 검증
            if not isinstance(image, Image.Image):
                raise ValueError("Invalid image type")
            if not isinstance(mask, np.ndarray):
                raise ValueError("Invalid mask type")
            
            # 크기 조정
            if image.size != (mask.shape[1], mask.shape[0]):
                mask = Image.fromarray(mask).resize(image.size, Image.NEAREST)
                mask = np.array(mask)
            
            # 마스크 적용
            np_img = np.array(image)
            mask = mask.astype(bool)
            np_img[~mask] = 0  # 배경 제거
            
            return Image.fromarray(np_img)
            
        except Exception as e:
            logger.error(f"Failed to crop animal region: {str(e)}")
            raise ClassificationError("동물 영역 추출 실패")

    def classify_animal(self, image: Image.Image, mask: np.ndarray) -> Dict[str, float]:
        """
        CLIP을 이용하여 동물 클래스 분류
        
        Args:
            image (Image.Image): 원본 이미지
            mask (np.ndarray): 세그멘테이션 마스크
            
        Returns:
            Dict: {
                "class": str,          # 예측된 동물 클래스
                "confidence": float,   # 예측 신뢰도
                "top3": List[Tuple[str, float]]  # 상위 3개 예측 결과
            }
            
        Raises:
            ClassificationError: 분류 실패 시
        """
        try:
            # 이미지 전처리
            cropped_img = self.crop_animal_region(image, mask)
            image_input = self.preprocess(cropped_img).unsqueeze(0).to(self.device)

            # 추론
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                logits_per_image = image_features @ self.text_features.T
                probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

            # Top 3 예측 결과 추출
            top3_idx = np.argsort(probs)[-3:][::-1]
            top3_results = [
                (self.ANIMAL_CLASSES[idx], float(probs[idx])) 
                for idx in top3_idx
            ]

            result = {
                "class": self.ANIMAL_CLASSES[top3_idx[0]],
                "confidence": float(probs[top3_idx[0]]),
                "top3": top3_results
            }
            
            logger.info(f"Classification successful: {result['class']} ({result['confidence']:.2%})")
            return result

        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            raise ClassificationError("동물 분류 실패")
            
    def __del__(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'model'):
                del self.model
            if hasattr(self, 'text_features'):
                del self.text_features
            torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
