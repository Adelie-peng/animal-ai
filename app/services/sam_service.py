import os
import torch
import numpy as np
from torchvision import transforms
from PIL import Image
from mobile_sam.build_sam import sam_model_registry

class SamService:
    def __init__(self, model_type, checkpoint_path, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = sam_model_registry[model_type](checkpoint=checkpoint_path).to(self.device)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize((1024, 1024)),
            transforms.ToTensor(),
        ])

    def segment(self, image_path, input_point, input_label=1):
        image = Image.open(image_path).convert("RGB")
        transformed_image = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            image_embedding = self.model.image_encoder(transformed_image)
            sparse_embeddings, dense_embeddings = self.model.prompt_encoder(
                points=(torch.tensor([[[input_point[0], input_point[1]]]], device=self.device),
                        torch.tensor([[input_label]], device=self.device)),
                boxes=None,
                masks=None,
            )
            low_res_masks, iou_predictions = self.model.mask_decoder(
                image_embeddings=image_embedding,
                image_pe=self.model.prompt_encoder.get_dense_pe(),
                sparse_prompt_embeddings=sparse_embeddings,
                dense_prompt_embeddings=dense_embeddings,
                multimask_output=False,
            )
            masks = self.model.postprocess_masks(
                low_res_masks, (1024, 1024), (1024, 1024)
            )
        return image, masks[0, 0].cpu().numpy(), iou_predictions[0, 0].item()

    def save_mask(self, mask_array, save_path, save_format='png'):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        if save_format == 'png':
            mask_img = Image.fromarray((mask_array * 255).astype(np.uint8))
            mask_img.save(save_path)
        elif save_format == 'npy':
            np.save(save_path, mask_array)
        else:
            raise ValueError("지원하지 않는 형식입니다: 'png' 또는 'npy' 중 하나를 선택하세요.")

# ✅ 전역 인스턴스 생성
sam_service = SamService(
    model_type="vit_t",
    checkpoint_path="E:/0. study/0. AI/AnImals/external/MobileSAM/weights/mobile_sam.pt"
)
