# app/services/model.py
import torch
import numpy as np
from mobile_sam import SamPredictor, sam_model_registry
from torchvision.transforms import ToTensor
from PIL import Image
import io
import logging
from pathlib import Path

# 로거 설정
logger = logging.getLogger(__name__)

# 모델 경로 설정
MODEL_PATH = Path(__file__).parent.parent.parent / 'external' / 'MobileSAM' / 'weights' / 'mobile_sam.pt'

# 장치 설정
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

# 모델 로드 (global 변수로)
try:
    sam = sam_model_registry["vit_t"](checkpoint=str(MODEL_PATH))
    sam.to(device=DEVICE)
    sam.eval()
    predictor = SamPredictor(sam)
    logger.info("Successfully loaded Mobile SAM model")
except Exception as e:
    logger.error(f"Failed to load Mobile SAM model: {str(e)}")
    raise

def segment_animal(image_bytes):
    """
    이미지 바이트 데이터에서 동물을 세그멘테이션합니다.
    
    Args:
        image_bytes: 이미지 바이트 데이터
        
    Returns:
        dict: 세그멘테이션 결과 정보
    """
    try:
        # 이미지 로드 및 변환
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(image)
        
        # 이미지 설정
        predictor.set_image(image_array)
        
        # 이미지 중앙에 포인트 설정 (기본 위치)
        h, w = image_array.shape[:2]
        input_point = np.array([[w // 2, h // 2]])
        input_label = np.array([1])  # 1은 foreground
        
        # 세그멘테이션 수행
        masks, scores, _ = predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True,
        )
        
        # 최고 점수의 마스크 선택
        best_mask_idx = np.argmax(scores)
        best_mask = masks[best_mask_idx]
        best_score = float(scores[best_mask_idx])
        
        # 마스크 영역에서 바운딩 박스 계산
        y_indices, x_indices = np.where(best_mask)
        if len(y_indices) > 0 and len(x_indices) > 0:
            x_min, x_max = int(np.min(x_indices)), int(np.max(x_indices))
            y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
            box = [x_min, y_min, x_max, y_max]
        else:
            box = [0, 0, w, h]  # 마스크가 없으면 전체 이미지 사용
        
        logger.info(f"Segmentation completed with score: {best_score:.4f}")
        
        return {
            "mask_shape": best_mask.shape,
            "mask_area": int(np.sum(best_mask)),
            "score": best_score,
            "box": box,
            "image_size": (h, w)
        }
    
    except Exception as e:
        logger.error(f"Segmentation failed: {str(e)}")
        raise Exception(f"Failed to segment animal: {str(e)}")