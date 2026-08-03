from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
from PIL import Image
import io
import cv2

# Import your real ELA math
from src.signals.ela import compute_ela

app = FastAPI()

# CRUCIAL: This allows your HTML file to talk to the Python server securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze/ela")
async def run_ela_endpoint(file: UploadFile = File(...)):
    """Receives an image from the UI, runs ELA, and returns a JPEG heatmap."""
    # 1. Read the uploaded file into a PIL Image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')
    
    # 2. Run the real Python math!
    ela_array = compute_ela(image, quality=90, scale=15)
    
    # 3. Convert the resulting NumPy array back into a JPEG image format
    is_success, buffer = cv2.imencode(".jpg", ela_array)
    io_buf = io.BytesIO(buffer)
    
    # 4. Send the actual image back to the dashboard
    return Response(content=io_buf.getvalue(), media_type="image/jpeg")

if __name__ == "__main__":
    print("Starting Forensics Backend Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)