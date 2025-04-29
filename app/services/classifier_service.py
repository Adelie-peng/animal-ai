import torch
import clip
import numpy as np
from PIL import Image
from typing import Tuple, Dict, List

class AnimalClassifier:
    def __init__(self):
        """CLIP 모델과 동물 클래스 초기화"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        
        # 동물 클래스 정의 (필요에 따라 확장 가능)
        self.ANIMAL_CLASSES: List[str] = [
            "a dog", "a cat", "a lion", "a tiger", "a bear",
            "a horse", "a panda", "a fox", "a rabbit", "a deer",
            "a wolf", "a monkey", "a elephant", "a giraffe", "a zebra"
        ]
        # 텍스트 임베딩 미리 계산
        self.text_inputs = clip.tokenize(
            [f"a photo of {cls}" for cls in self.ANIMAL_CLASSES]
        ).to(self.device)
        with torch.no_grad():
            self.text_features = self.model.encode_text(self.text_inputs)

    def crop_animal_region(self, image: Image.Image, mask: np.ndarray) -> Image.Image:
        """세그멘테이션 마스크를 이용해 동물 영역만 잘라냄"""
        # 이미지와 마스크 크기가 다른 경우 처리
        if image.size != (mask.shape[1], mask.shape[0]):
            mask = Image.fromarray(mask).resize(image.size, Image.NEAREST)
            mask = np.array(mask)
        
        np_img = np.array(image)
        mask = mask.astype(bool)
        np_img[~mask] = 0  # 배경 제거
        return Image.fromarray(np_img)

    def classify_animal(self, image: Image.Image, mask: np.ndarray) -> Dict[str, float]:
        """
        CLIP을 이용하여 동물 클래스 분류
        Args:
            image: PIL.Image 원본 이미지
            mask: segmentation 결과 마스크 (numpy.ndarray)
        Returns:
            딕셔너리: {"class": 예측된_클래스, "confidence": 신뢰도, 
                     "top3": [(클래스1, 신뢰도1), (클래스2, 신뢰도2), ...]}
        """
        cropped_img = self.crop_animal_region(image, mask)
        image_input = self.preprocess(cropped_img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            # 미리 계산된 텍스트 특징 사용
            logits_per_image = image_features @ self.text_features.T
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

        # Top 3 예측 결과 추출
        top3_idx = np.argsort(probs)[-3:][::-1]
        top3_results = [
            (self.ANIMAL_CLASSES[idx], float(probs[idx])) 
            for idx in top3_idx
        ]

        return {
            "class": self.ANIMAL_CLASSES[top3_idx[0]],
            "confidence": float(probs[top3_idx[0]]),
            "top3": top3_results
        }
