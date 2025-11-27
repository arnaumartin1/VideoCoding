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

# Classes of Seminar 2:
class VideoResolution(BaseModel):
    video_filename: str = "big_buck_bunny.mp4"
    width: int = Body(..., gt=0)
    height: int = Body(..., gt=0)

class ChromaSubsampling(BaseModel):
    video_filename: str = "big_buck_bunny.mp4"
    pixel_format: str = Body(...)

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

@app.post("/video/resize/")
async def resize_video(resolution_data: VideoResolution):
    width = resolution_data.width
    height = resolution_data.height
    input_filename = resolution_data.video_filename
    
    shared_dir = "/shared"
    media_dir = "/app/media"
    
    if input_filename == "big_buck_bunny.mp4":
        input_path = os.path.join(media_dir, input_filename)
        if not os.path.exists(input_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Video '{input_filename}' not found in {media_dir}. Please make sure to download it."
            )
        # Generate output filename
        file_id = str(uuid.uuid4())
        output_filename = f"resized_bbb_{width}x{height}_{file_id}.mp4"
    else:
        input_path = os.path.join(shared_dir, input_filename)
        # Logic to handle error or support uploaded files
        raise HTTPException(
            status_code=400, 
            detail="For simplicity, this endpoint only expects 'big_buck_bunny.mp4' as `video_filename`."
        )

    output_path = os.path.join(shared_dir, output_filename) # Output in shared volume
    
    try:
        (   
            ffmpeg
            .input(input_path)
            .filter('scale', width, height)
            .output(output_path, vcodec='libx264', acodec='aac') 
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        # Return response
        return {
            "message": "Video resized successfully",
            "output_file": output_filename,
            "dimensions": {"width": width, "height": height},
            "note": f"Original video: {input_filename}. Output file saved in shared volume at {output_path}"
        }
    
    except ffmpeg.Error as e: # Catch ffmpeg errors
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    
    except Exception as e: # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
@app.post("/video/chroma_subsampling/")
async def chroma_subsampling(subsampling_data: ChromaSubsampling):
    input_filename = subsampling_data.video_filename
    pixel_format = subsampling_data.pixel_format.lower()

    # We use format strings compatible with FFmpeg
    valid_formats = ["yuv420p", "yuv422p", "yuv444p"]
    if pixel_format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pixel format. Use one of: {valid_formats}"
        )

    media_dir = "/app/media" # path to media files
    shared_dir = "/shared"
    
    # We use only big_buck_bunny.mp4 for simplicity
    if input_filename == "big_buck_bunny.mp4":
        input_path = os.path.join(media_dir, input_filename)
        if not os.path.exists(input_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Video '{input_filename}' not found in {media_dir}. Please make sure to download it."
            )
        
        # Generate output filename in shared volume
        file_id = str(uuid.uuid4())
        output_filename = f"chroma_{pixel_format}_{file_id}.mp4"
    else:
        # Logic to handle error or support uploaded files
        raise HTTPException(
            status_code=400, 
            detail="For simplicity, this endpoint only expects 'big_buck_bunny.mp4' as `video_filename`."
        )

    output_path = os.path.join(shared_dir, output_filename)
    
    try:
        # We use the '-pix_fmt' argument to force chroma subsampling
        (
            ffmpeg
            .input(input_path)
            .output(output_path, vcodec='libx264', acodec='aac', pix_fmt=pixel_format)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        return {
            "message": "Chroma subsampling modified successfully",
            "output_file": output_filename,
            "new_pixel_format": pixel_format,
            "note": f"Output file saved in shared volume at {output_path}"
        }
    
    except ffmpeg.Error as e: # Catch ffmpeg errors
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    
    except Exception as e: # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
@app.post("/video/multitrack/")
async def create_multitrack_video():
    """
    Create a multitrack video with:
    - Video cut to 20 seconds
    - Audio track 1: AAC mono (128k)
    - Audio track 2: MP3 stereo (64k)
    - Audio track 3: AC3 (192k)
    """
    input_path = "/app/media/big_buck_bunny.mp4"
    shared_dir = "/shared"
    output_filename = f"multitrack_{uuid.uuid4()}.mp4"
    output_path = os.path.join(shared_dir, output_filename)

    try:
        # Use subprocess approach for complex multi-track encoding
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-t', '20',  # Cut to 20 seconds
            '-map', '0:v:0',  # Map video
            '-map', '0:a:0',  # Map audio for track 1 (AAC mono)
            '-map', '0:a:0',  # Map audio for track 2 (MP3 stereo)
            '-map', '0:a:0',  # Map audio for track 3 (AC3)
            '-c:v', 'libx264',  # Video codec
            # Audio track 0: AAC mono
            '-c:a:0', 'aac',
            '-ac:a:0', '1',
            '-b:a:0', '128k',
            # Audio track 1: MP3 stereo with lower bitrate
            '-c:a:1', 'libmp3lame',
            '-ac:a:1', '2',
            '-b:a:1', '64k',
            # Audio track 2: AC3
            '-c:a:2', 'ac3',
            '-b:a:2', '192k',
            '-y',  # Overwrite output
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"FFmpeg error: {result.stderr}"
            )

        return {
            "message": "Multitrack video created successfully",
            "output_file": output_filename,
            "tracks": {
                "video": "H.264 (20s)",
                "audio_0": "AAC mono @ 128k",
                "audio_1": "MP3 stereo @ 64k",
                "audio_2": "AC3 @ 192k"
            }
        }

    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    
@app.post("/video/visualize_coding/")
async def visualize_coding_info(video_filename: str = Body("big_buck_bunny.mp4")):
    """
    Outputs a video showing the macroblocks and motion vectors using FFmpeg's codecview filter.
    Uses special decoder flags to export motion vector data during decoding.
    """
    media_dir = "/app/media"
    shared_dir = "/shared"
    
    if video_filename != "big_buck_bunny.mp4":
         raise HTTPException(
             status_code=400, 
             detail="For simplicity, this endpoint only expects 'big_buck_bunny.mp4' as `video_filename`."
         )

    input_path = os.path.join(media_dir, video_filename)
    if not os.path.exists(input_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Video '{video_filename}' not found in {media_dir}."
        )

    file_id = str(uuid.uuid4())
    output_filename = f"codecview_{file_id}.mp4"
    output_path = os.path.join(shared_dir, output_filename)
    
    # codecview filter to visualize blocks and motion vectors
    # mv=pf+bf+bb shows all motion vector types (P-forward, B-forward, B-backward)
    codecview_filter = 'codecview=mv=pf+bf+bb:block=1'
    
    try:
        # CRITICAL: Use flags2=+export_mvs to export motion vectors during decoding
        # This makes the decoder expose motion vector information to the codecview filter
        (
            ffmpeg
            .input(input_path, flags2='export_mvs')  # Export motion vectors from decoder
            .output(
                output_path, 
                vcodec='libx264',
                vf=codecview_filter,
                acodec='aac' 
            ) 
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        return {
            "message": "Video with coding info generated successfully",
            "output_file": output_filename,
            "filter_applied": codecview_filter,
            "note": "Motion vectors extracted from original video during decoding using flags2=export_mvs."
        }
    
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
