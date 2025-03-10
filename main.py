from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
import os
import zipfile
from services import extract_reel, generate_thumbnail, generate_caption, create_multiple_highlight_reels

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ReelRequest(BaseModel):
    start_time: float
    end_time: float

class ThumbnailRequest(BaseModel):
    timestamp: float

class CaptionRequest(BaseModel):
    prompt_overrides: str = None

class HighlightRequest(BaseModel):
    target_duration: int = 60

def save_upload_file(upload_file: UploadFile) -> str:
    if not upload_file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video file.")
    
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

@app.post("/reel/")
async def create_reel(file: UploadFile = File(...), start_time: float = Form(...), end_time: float = Form(...)):
    input_path = save_upload_file(file)
    output_path = os.path.join(OUTPUT_DIR, "reel.mp4")
    
    try:
        if start_time < 0:
            raise HTTPException(status_code=400, detail="Start time cannot be negative")
        result_path = extract_reel(input_path, start_time, end_time, output_path)
        return FileResponse(result_path, media_type="video/mp4", filename="reel.mp4")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.post("/thumbnail/")
async def create_thumbnail(file: UploadFile = File(...), timestamp: float = Form(...)):
    input_path = save_upload_file(file)
    output_path = os.path.join(OUTPUT_DIR, "thumbnail.jpg")
    
    try:
        if timestamp < 0:
            raise HTTPException(status_code=400, detail="Timestamp cannot be negative")
        result_path = generate_thumbnail(input_path, timestamp, output_path)
        return FileResponse(result_path, media_type="image/jpeg", filename="thumbnail.jpg")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.post("/caption/")
async def create_caption(file: UploadFile = File(...), prompt_overrides: str = Form(None)):
    input_path = save_upload_file(file)
    
    try:
        caption = generate_caption(input_path, prompt_overrides)
        return {"caption": caption}
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.post("/highlight-reels/")
async def create_highlight_reels(
    file: UploadFile = File(...),
    target_duration: float = Form(60.0),
    num_reels: int = Form(5)
):
    if target_duration <= 0:
        raise HTTPException(status_code=400, detail="Target duration must be positive")
    if num_reels <= 0 or num_reels > 10:
        raise HTTPException(status_code=400, detail="Number of reels must be between 1 and 10")
    
    input_path = save_upload_file(file)
    output_dir = OUTPUT_DIR
    
    try:
        result_paths = create_multiple_highlight_reels(
            input_path,
            output_dir,
            target_duration=target_duration,
            num_reels=num_reels
        )
        
        zip_path = os.path.join(output_dir, "highlight_reels.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for path in result_paths:
                zipf.write(path, os.path.basename(path))
                # Clean up individual reel files after adding to zip
                os.remove(path)
                
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="highlight_reels.zip"
        )
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.post("/cleanup/")
async def cleanup_directories():
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)
    return {"status": "Cleanup completed", "directories_cleaned": [UPLOAD_DIR, OUTPUT_DIR]}

@app.get("/health/")
async def health_check():
    return {
        "status": "healthy",
        "upload_dir": os.path.exists(UPLOAD_DIR),
        "output_dir": os.path.exists(OUTPUT_DIR)
    }
