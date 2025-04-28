from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.scrapper import scrape_animal_info, korean_to_english

router = APIRouter()

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()
    animal_name = file.filename.split('.')[0].lower()
    animal_info = scrape_animal_info(animal_name)

    return JSONResponse(content={
        "filename": file.filename,
        "predicted_animal": animal_name,
        "animal_info": animal_info,
        "file_size": len(contents)
    })

@router.get("/text/{animal_kr}")
async def get_animal_info(animal_kr: str):
    animal_en = korean_to_english(animal_kr)
    animal_info = scrape_animal_info(animal_en)

    return JSONResponse(content={
        "input": animal_kr,
        "translated": animal_en,
        "animal_info": animal_info,
    })
