# 분류 결과 디버깅을 위한 스크립트
# utils/debug_classification.py

import torch
import clip
from PIL import Image
import matplotlib.pyplot as plt

# CLIP 모델 로드
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# 동물 클래스 정의 (CLIP에서 사용하는 것과 동일)
animal_classes = [
    "a dog", "a cat", "a lion", "a tiger", "a bear",
    "a horse", "a panda", "a fox", "a rabbit", "a deer",
    "a wolf", "a monkey", "a elephant", "a giraffe", "a zebra"
]

# 이미지 로드 (테스트용)
def test_classification(image_path):
    image = Image.open(image_path)
    image_input = preprocess(image).unsqueeze(0).to(device)
    text_inputs = clip.tokenize([f"a photo of {cls}" for cls in animal_classes]).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image_input)
        text_features = model.encode_text(text_inputs)
        
        logits_per_image = image_features @ text_features.T
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]

    # 상위 5개 결과 출력
    top5_idx = probs.argsort()[-5:][::-1]
    
    print("Top 5 분류 결과:")
    for idx in top5_idx:
        print(f"{animal_classes[idx]}: {probs[idx]:.2%}")
    
    # 시각화
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(probs)), probs)
    ax.set_xticks(range(len(animal_classes)))
    ax.set_xticklabels(animal_classes, rotation=45, ha='right')
    ax.set_ylabel('확률')
    ax.set_title('CLIP 동물 분류 결과')
    plt.tight_layout()
    plt.savefig('classification_results.png')
    plt.close()
    
    return animal_classes[top5_idx[0]]

# 사용 예:
# result = test_classification("deer_image.jpg")
# print(f"최종 분류 결과: {result}")
