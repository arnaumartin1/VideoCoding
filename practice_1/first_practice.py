from fastapi import FastAPI, Body, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Create shared directory if it doesn't exist to save files
SHARED_DIR = "/shared"
if not os.path.exists(SHARED_DIR):
    os.makedirs(SHARED_DIR)

# Mount shared directory to serve files
app.mount("/files", StaticFiles(directory=SHARED_DIR), name="files")

@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
        
        download_url = f"/files/{output_filename}" 

        return {
            "message": "Image resized successfully",
            "output_file": output_filename,
            "saved_in": download_url,
            "dimensions": {"width": width, "height": height},
            "note": "File stored in shared volume, accessible by ffmpeg_tool container"
        }
    
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {error_message}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Exercise 1 of Seminar 2 Endpoint - Change video resolution

@app.post("/video/resize/")
async def resize_video(width: int,height: int,file: UploadFile = File(...)
):
    file_id = str(uuid.uuid4())
    input_ext = os.path.splitext(file.filename)[1]
    input_path = f"input_{file_id}{input_ext}"
    output_filename = f"resized_{width}x{height}_{file_id}.mp4"
    output_path = os.path.join("/shared", output_filename)

    with open(input_path, "wb") as f:
        f.write(await file.read())

    (
        ffmpeg
        .input(input_path)
        .filter("scale", width, height)
        .output(output_path, vcodec="libx264", acodec="aac")
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

    os.remove(input_path)

    download_url = f"/files/{output_filename}"

    return {
        "message": "Video resized successfully",
        "output_file": output_filename,
        "dimensions": {
            "width": width,
            "height": height
        },
        "saved_in": download_url
    }

# Exercise 2 of Seminar 2 Endpoint - Change chroma subsampling

@app.post("/video/chroma_subsampling/")
async def chroma_subsampling(pixel_format: str,file: UploadFile = File(...)
):
    pixel_format = pixel_format.lower()
    valid_formats = ["yuv420p", "yuv422p", "yuv444p"]

    if pixel_format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pixel format. Use one of: {valid_formats}"
        )

    file_id = str(uuid.uuid4())
    input_ext = os.path.splitext(file.filename)[1]
    input_path = f"input_{file_id}{input_ext}"
    output_filename = f"chroma_{pixel_format}_{file_id}.mp4"
    output_path = os.path.join("/shared", output_filename)

    with open(input_path, "wb") as f:
        f.write(await file.read())

    (
        ffmpeg
        .input(input_path)
        .output(
            output_path,
            vcodec="libx264",
            acodec="aac",
            pix_fmt=pixel_format
        )
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

    os.remove(input_path)

    download_url = f"/files/{output_filename}"

    return {
        "message": "Chroma subsampling modified successfully",
        "output_file": output_filename,
        "new_pixel_format": pixel_format,
        "saved_in": download_url
    }

    
# Exercise 3 of Seminar 2 Endpoint - Visualize coding info
@app.post("/video/info/")
async def video_info(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = f"input_{file_id}{os.path.splitext(file.filename)[1]}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Read the video info using ffmpeg
    probe = ffmpeg.probe(input_path)
    format_info = probe['format']
    streams_info = probe['streams']

    video_info = {
        "filename": file.filename,
        "format_name": format_info["format_name"],
        "duration_sec": float(format_info["duration"]),
        "size_bytes": int(format_info["size"]),
        "width": int(streams_info[0]["width"]),
        "height": int(streams_info[0]["height"]),

    }
    os.remove(input_path)

    return {"video_info": video_info}


# Exercise 4 of Seminar 2 Endpoint - Create multitrack video
  
@app.post("/video/multitrack/")
async def create_multitrack_video(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    input_ext = os.path.splitext(file.filename)[1]
    input_path = f"input_{file_id}{input_ext}"
    output_filename = f"multitrack_{file_id}.mp4"
    output_path = os.path.join("/shared", output_filename)

    with open(input_path, "wb") as f:
        f.write(await file.read())

    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-t', '20',
        '-map', '0:v:0',
        '-map', '0:a:0',
        '-map', '0:a:0',
        '-map', '0:a:0',
        '-c:v', 'libx264',

        # Audio track 0: AAC mono
        '-c:a:0', 'aac',
        '-ac:a:0', '1',
        '-b:a:0', '128k',

        # Audio track 1: MP3 stereo
        '-c:a:1', 'libmp3lame',
        '-ac:a:1', '2',
        '-b:a:1', '64k',

        # Audio track 2: AC3
        '-c:a:2', 'ac3',
        '-b:a:2', '192k',

        '-y',
        output_path
    ]

    subprocess.run(cmd, capture_output=True, text=True, check=True)

    os.remove(input_path)

    download_url = f"/files/{output_filename}"

    return {
        "message": "Multitrack video created successfully",
        "output_file": output_filename,
        "tracks": {
            "video": "H.264 (20s)",
            "audio_0": "AAC mono @ 128k",
            "audio_1": "MP3 stereo @ 64k",
            "audio_2": "AC3 @ 192k"
        },
        "saved_in": download_url
    }


# Exercise 5 of Seminar 2 Endpoint - Video streams info
@app.post("/video/streams/")
async def video_streams(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = f"input_{file_id}{os.path.splitext(file.filename)[1]}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Read the video streams using ffmpeg
    probe = ffmpeg.probe(input_path)
    streams = probe.get('streams', [])
    num_streams = len(streams)

    os.remove(input_path)

    return {"num_streams": num_streams}


# Exercise 6 of Seminar 2 Endpoint - Video Macroblocks and Motion Vectors Visualization

@app.post("/video/visualize_coding/")
async def visualize_coding_info(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    input_ext = os.path.splitext(file.filename)[1]
    input_path = f"input_{file_id}{input_ext}"
    output_filename = f"codecview_{file_id}.mp4"
    output_path = os.path.join("/shared", output_filename)

    with open(input_path, "wb") as f:
        f.write(await file.read())

    # codecview filter
    codecview_filter = "codecview=mv=pf+bf+bb:block=1"

    (
        ffmpeg
        .input(input_path, flags2="export_mvs")
        .output(
            output_path,
            vcodec="libx264",
            vf=codecview_filter,
            acodec="aac"
        )
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )

    os.remove(input_path)

    download_url = f"/files/{output_filename}"

    return {
        "message": "Video with coding info generated successfully",
        "output_file": output_filename,
        "filter_applied": codecview_filter,
        "saved_in": download_url
    }


# Exercise 7 of Seminar 2 Endpoint - Video YUV Histogram Visualization

@app.post("/video/yuv-histogram/")
async def video_yuv_histogram(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    input_filename = f"input_{file_id}{os.path.splitext(file.filename)[1]}"
    output_filename = f"yuv_hist_{file_id}.mp4"

    shared_dir = "/shared"
    input_path = os.path.join(shared_dir, input_filename)
    output_path = os.path.join(shared_dir, output_filename)

    # Save video
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Direct FFmpeg command (simple and safe)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf",
        "format=yuv420p,extractplanes=y+u+v[y][u][v];"
        "[y]histogram[yh];"
        "[u]histogram[uh];"
        "[v]histogram[vh];"
        "[yh][uh][vh]vstack=3",
        output_path
    ]

    subprocess.run(cmd)

    os.remove(input_path)

    return FileResponse(output_path, media_type="video/mp4", filename=output_filename)


# Exercise 1 of Practice 2 Endpoint - Convert input video to 4 formats

@app.post("/video/convert_video_4_formats/")
async def convert_codecs(file: UploadFile = File(...)):

    uid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    input_path = f"input_{uid}{ext}"

    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Output paths
    vp8_output = f"/shared/vp8_{uid}.webm"
    vp9_output = f"/shared/vp9_{uid}.webm"
    h265_output = f"/shared/h265_{uid}.mp4"
    av1_output = f"/shared/av1_{uid}.mkv"

    # ffmpeg commands for each format
    # VP8
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-c:v", "libvpx", vp8_output],
        check=True
    )

    # VP9
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-c:v", "libvpx-vp9", vp9_output],
        check=True
    )

    # H.265
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-c:v", "libx265", h265_output],
        check=True
    )

    # AV1
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-c:v", "libaom-av1", av1_output],
        check=True
    )

    os.remove(input_path)

    return {
        "message": "Video converted to all codecs successfully",
        "vp8": vp8_output,
        "vp9": vp9_output,
        "h265": h265_output,
        "av1": av1_output
    }


# Exercise 2 of Practice 2 Endpoint - Encoding ladder

# Reused 2 endpoints as an interal functions
def resize_video(input_path: str, width: int, height: int) -> str:
    uid = str(uuid.uuid4())
    output_path = f"/shared/ladder_{width}x{height}_{uid}.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={width}:{height}",
            "-c:v", "libx264",
            output_path
        ],
        check=True
    )

    return output_path


# Reused function converted to only H.265

def convert_to_h265(input_path: str, bitrate: str) -> str:
    uid = str(uuid.uuid4())
    output_path = f"/shared/ladder_{bitrate}_{uid}.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_path,
            "-c:v", "libx265",
            "-b:v", bitrate,
            output_path
        ],
        check=True
    )

    return output_path


# Endpoint that creates an encoding ladder calling the previous 2 functions

@app.post("/video/encoding_ladder/")
async def encoding_ladder(file: UploadFile = File(...)):

    uid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    input_path = f"input_{uid}{ext}"

    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Our ladder will do 3 configurations: 1920x1080@4000k, 1280x720@2500k, 854x480@1000k
    ladder_config = [
        {"width": 1920, "height": 1080, "bitrate": "4000k"},
        {"width": 1280, "height": 720,  "bitrate": "2500k"},
        {"width": 854,  "height": 480,  "bitrate": "1000k"},
    ]

    outputs = []

    for level in ladder_config:
        # 1. Resize using internal function
        resized_path = resize_video(
            input_path,
            level["width"],
            level["height"]
        )

        # 2. Encode using internal function
        encoded_path = convert_to_h265(
            resized_path,
            level["bitrate"]
        )

        outputs.append({
            "resolution": f'{level["width"]}x{level["height"]}',
            "bitrate": level["bitrate"],
            "file": encoded_path
        })

        os.remove(resized_path)

    os.remove(input_path)

    return {
        "message": "Encoding ladder created successfully",
        "ladder": outputs
    }





