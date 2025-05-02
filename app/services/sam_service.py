import os
import torch
import numpy as np
from torchvision import transforms
from PIL import Image
from typing import Tuple, Optional, Union
from dataclasses import dataclass
import logging
from mobile_sam import sam_model_registry
from mobile_sam.predictor import SamPredictor
from pathlib import Path

# 로거 설정
logger = logging.getLogger(__name__)

@dataclass
class SegmentationError(Exception):
    """세그멘테이션 과정에서 발생하는 예외를 처리하는 클래스"""
    message: str
    details: Optional[dict] = None

class SamService:
    """MobileSAM을 사용한 이미지 세그멘테이션 서비스"""
    
    def __init__(self, model_type: str = "vit_t"):
        """
        MobileSAM 서비스 초기화
        
        Args:
            model_type: 모델 타입 (기본값: "vit_t")
        """
        try:
            # 모델 가중치 경로 설정
            self.model_path = Path(__file__).parent.parent.parent / 'external' / 'MobileSAM' / 'weights' / 'mobile_sam.pt'
            if not self.model_path.exists():
                raise FileNotFoundError(f"모델 가중치를 찾을 수 없습니다: {self.model_path}")
                
            # 장치 설정
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
            # 모델 로드
            self.model = sam_model_registry[model_type](checkpoint=str(self.model_path))
            self.model.to(device=self.device)
            self.model.eval()
            
            # 이미지 전처리 설정
            self.transform = transforms.Compose([
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # 프리딕터 초기화
            self.predictor = SamPredictor(self.model)
            
            logger.info(f"SamService initialized with model_type: {model_type}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SamService: {str(e)}")
            raise SegmentationError("서비스 초기화 실패", {"error": str(e)})

    def segment(self, image_path: Union[str, bytes], 
                input_point: Tuple[int, int], 
                input_label: int = 1) -> Tuple[Image.Image, np.ndarray, float]:
        """
        이미지 세그멘테이션 수행
        
        Args:
            image_path: 이미지 파일 경로 또는 바이트 데이터
            input_point: 세그멘테이션 기준점 (x, y)
            input_label: 레이블 (기본값: 1, foreground)
            
        Returns:
            Tuple[Image.Image, np.ndarray, float]: (원본 이미지, 마스크, IoU 점수)
            
        Raises:
            SegmentationError: 세그멘테이션 실패 시
        """
        try:
            # 이미지 로드
            if isinstance(image_path, str):
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image file not found: {image_path}")
                image = Image.open(image_path).convert("RGB")
            else:
                image = Image.open(image_path).convert("RGB")
            
            # 이미지 전처리
            transformed_image = self.transform(image).unsqueeze(0).to(self.device)
            
            # 세그멘테이션 수행
            with torch.no_grad():
                # 이미지 임베딩
                image_embedding = self.model.image_encoder(transformed_image)
                
                # 프롬프트 인코딩
                points = torch.tensor([[[input_point[0], input_point[1]]]], device=self.device)
                labels = torch.tensor([[input_label]], device=self.device)
                
                sparse_embeddings, dense_embeddings = self.model.prompt_encoder(
                    points=(points, labels),
                    boxes=None,
                    masks=None,
                )
                
                # 마스크 디코딩
                low_res_masks, iou_predictions = self.model.mask_decoder(
                    image_embeddings=image_embedding,
                    image_pe=self.model.prompt_encoder.get_dense_pe(),
                    sparse_prompt_embeddings=sparse_embeddings,
                    dense_prompt_embeddings=dense_embeddings,
                    multimask_output=False,
                )
                
                # 마스크 후처리
                masks = self.model.postprocess_masks(
                    low_res_masks, (1024, 1024), (1024, 1024)
                )
                
            logger.debug(f"Segmentation completed with IoU: {iou_predictions[0, 0].item():.4f}")
            return image, masks[0, 0].cpu().numpy(), iou_predictions[0, 0].item()
            
        except Exception as e:
            logger.error(f"Segmentation failed: {str(e)}")
            raise SegmentationError("세그멘테이션 실패", {"error": str(e)})

    def save_mask(self, mask_array: np.ndarray, save_path: str, save_format: str = 'png') -> None:
        """
        세그멘테이션 마스크 저장
        
        Args:
            mask_array: 마스크 배열
            save_path: 저장 경로
            save_format: 저장 형식 ('png' 또는 'npy')
            
        Raises:
            ValueError: 지원하지 않는 저장 형식
            SegmentationError: 마스크 저장 실패 시
        """
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            if save_format == 'png':
                mask_img = Image.fromarray((mask_array * 255).astype(np.uint8))
                mask_img.save(save_path)
            elif save_format == 'npy':
                np.save(save_path, mask_array)
            else:
                raise ValueError("지원하지 않는 형식입니다: 'png' 또는 'npy' 중 하나를 선택하세요.")
                
            logger.info(f"Mask saved successfully: {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save mask: {str(e)}")
            raise SegmentationError("마스크 저장 실패", {"error": str(e)})

    def __del__(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'model'):
                del self.model
            torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

# 전역 인스턴스 생성
try:
    sam_service = SamService(model_type="vit_t")
    logger.info("Global SAM service instance created successfully")
except Exception as e:
    logger.critical(f"Failed to create global SAM service instance: {str(e)}")
    raise