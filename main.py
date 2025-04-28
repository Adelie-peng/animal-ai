from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()
    
    # 최소 구조로 세팅, 파일을 받고 리턴만. (추후 AI 모델 호출 코드 추가)
    return JSONResponse(content={
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    })

# conda create -n animal-ai --file requirements.txt
# pip freeze > requirements.txt
# 위 명령어 둘 중 하나로 환경 복원 가능.