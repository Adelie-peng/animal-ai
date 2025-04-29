# app/services/model.py
import torch
from mobile_sam import SamPredictor, sam_model_registry
from torchvision.transforms import ToTensor
from PIL import Image
import io

# 모델 로드 (global 변수로)
sam = sam_model_registry["vit_t"](checkpoint="external/MobileSAM/weights/mobile_sam.pt")
sam.to(device="cuda" if torch.cuda.is_available() else "cpu")
predictor = SamPredictor(sam)

def segment_animal(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_tensor = ToTensor()(image).unsqueeze(0)

    predictor.set_image(image_tensor[0].cpu().numpy())

    # Dummy box (실제론 CLIP 결과로 box 추정 예정)
    dummy_box = [100, 100, 300, 300]  # xmin, ymin, xmax, ymax

    masks, _, _ = predictor.predict(box=dummy_box, multimask_output=False)

    return {
        "mask_shape": masks.shape,
        "dummy_box_used": dummy_box
    }
