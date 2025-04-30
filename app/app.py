from fastapi import FastAPI
from app.routers import analyze

app = FastAPI()
app.include_router(analyze.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API is alive"}
