from fastapi import FastAPI, Body, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services import ColorTranslator
import subprocess
import tempfile
import os
import uuid
import ffmpeg

# Classes of Seminar 1:
class RGB(BaseModel):
    R: int = Body(..., ge=0, le=255)
    G: int = Body(..., ge=0, le=255)
    B: int = Body(..., ge=0, le=255)

class YUV(BaseModel):
    Y: int = Body(..., ge=0, le=255)
    U: int = Body(..., ge=0, le=255)
    V: int = Body(..., ge=0, le=255)

# Service wrapper functions
def rgb_to_yuv_service(R: int, G: int, B: int):
    return ColorTranslator.rgb_to_yuv(R, G, B)

def yuv_to_rgb_service(Y: int, U: int, V: int):
    return ColorTranslator.yuv_to_rgb(Y, U, V)

app = FastAPI(title="FastAPI for Practice 1")

@app.get("/")
def read_root(): # Endpoint to check if the API is running
    return {"message": "FastAPI for Practice 1 running successfully!"}

# Exercise 2 of Seminar 1 Endpoint
@app.post("/convert/rgb_to_yuv/")
def convert_rgb_to_yuv(rgb: RGB):
    return rgb_to_yuv_service(rgb.R, rgb.G, rgb.B)

@app.post("/convert/yuv_to_rgb/")
def convert_yuv_to_rgb(yuv: YUV):
    return yuv_to_rgb_service(yuv.Y, yuv.U, yuv.V)

# Exercise 3 of Seminar 1 Endpoint - Using ffmpeg-python library
@app.post("/image/resize/")
async def resize_image(width: int, height: int, file: UploadFile = File(...)):
    """Resize an image using ffmpeg-python library"""
    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Width and height must be positive.")
    
    try:
        # Generate unique filenames
        file_id = str(uuid.uuid4())
        input_filename = f"input_{file_id}{os.path.splitext(file.filename)[1]}"
        output_filename = f"resized_{file_id}.jpg"
        
        # Paths in shared volume (accessible by ffmpeg_tool container too)
        shared_dir = "/shared"
        input_path = os.path.join(shared_dir, input_filename)
        output_path = os.path.join(shared_dir, output_filename)
        
        # Save uploaded file to shared volume
        with open(input_path, "wb") as f:
            f.write(await file.read())
        
        # Use ffmpeg-python to resize the image
        # This will be processed and stored in the shared volume
        (
            ffmpeg
            .input(input_path)
            .filter('scale', width, height)
            .output(output_path, y=None)  # y=None means overwrite without asking
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Clean up input file
        if os.path.exists(input_path):
            os.remove(input_path)
        
        return {
            "message": "Image resized successfully",
            "output_file": output_filename,
            "dimensions": {"width": width, "height": height},
            "note": "File stored in shared volume, accessible by ffmpeg_tool container"
        }
    
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New endpoint: Convert video format using ffmpeg-python library
@app.post("/video/convert/")
async def convert_video(output_format: str, file: UploadFile = File(...)):
    """Convert a video to a different format using ffmpeg-python library"""
    valid_formats = ["mp4", "avi", "mkv", "webm", "mov"]
    if output_format.lower() not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Output format must be one of: {valid_formats}")
    
    try:
        # Generate unique filenames
        file_id = str(uuid.uuid4())
        input_filename = f"input_{file_id}{os.path.splitext(file.filename)[1]}"
        output_filename = f"converted_{file_id}.{output_format.lower()}"
        
        # Paths in shared volume (accessible by ffmpeg_tool container too)
        shared_dir = "/shared"
        input_path = os.path.join(shared_dir, input_filename)
        output_path = os.path.join(shared_dir, output_filename)
        
        # Save uploaded file to shared volume
        with open(input_path, "wb") as f:
            f.write(await file.read())
        
        # Use ffmpeg-python to convert the video
        (
            ffmpeg
            .input(input_path)
            .output(output_path)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Clean up input file
        if os.path.exists(input_path):
            os.remove(input_path)
        
        return {
            "message": "Video converted successfully",
            "output_file": output_filename,
            "output_format": output_format.lower(),
            "note": "File stored in shared volume, accessible by ffmpeg_tool container"
        }
    
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
