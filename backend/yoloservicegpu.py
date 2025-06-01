import io
import base64
import asyncio
from typing import List, Optional

import torch
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from PIL import Image
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
from torchvision import transforms

from app.utilities import config

app = FastAPI()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ─── Load models once at startup and move to DEVICE ─────────────────────────────
# YOLO (Ultralytics) will automatically run on CUDA if available when you .to(DEVICE),
# but under the hood, you may need to call yolov5.cuda() or rely on Ultralytics to pick CUDA.
yolo = YOLO(config.MODEL_PATH)
yolo.model.to(DEVICE)  # ensure YOLO backbone is on GPU

facenet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)

# ─── Common image‐to‐tensor transform (for all face crops) ──────────────────────
_transform = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5],
                         std=[0.5, 0.5, 0.5]),
])

# ─── Pydantic models (if you want stricter validation) ──────────────────────────
class BoxesRequest(BaseModel):
    padding: Optional[int] = None

class CropRequest(BaseModel):
    boxes: List[List[float]]  # List of [x1, y1, x2, y2]

class VectorFaceResponse(BaseModel):
    vector: List[float]

class VectorFacesResponse(BaseModel):
    vectors: List[List[float]]


def pil_from_uploadfile(file: UploadFile) -> Image.Image:
    """
    Read an UploadFile into a PIL Image (RGB).
    We read file.file.read() once per endpoint.
    """
    contents = file.file.read()
    return Image.open(io.BytesIO(contents)).convert("RGB")


# ─── Helper: Run YOLO inference in a threadpool ─────────────────────────────────
def _sync_yolo_inference(pil_img: Image.Image) -> List[List[float]]:
    """
    Run YOLO on a PIL image (already loaded) and return raw boxes (cpu numpy list).
    This function runs *synchronously* on the current process, but we will call it
    inside run_in_executor(...) to avoid blocking the event loop.
    """
    # YOLO from ultralytics: pass PIL directly (will convert internally).
    results = yolo(pil_img)  # runs on GPU if model is on DEVICE
    raw_boxes = results[0].boxes.xyxy.cpu().numpy().tolist()
    return raw_boxes


# ─── Helper: Batch FaceNet embeddings ───────────────────────────────────────────
def _sync_facenet_batch(face_pil_list: List[Image.Image]) -> List[List[float]]:
    """
    Given a list of PIL face crops, apply the transform, stack into one tensor,
    move to DEVICE, run through facenet, and return a list of lists (embeddings).
    """
    if len(face_pil_list) == 0:
        return []

    # Transform each PIL → tensor (3×160×160), then stack → (N, 3, 160, 160)
    tensors = [ _transform(face).unsqueeze(0) for face in face_pil_list ]
    batch_tensor = torch.cat(tensors, dim=0).to(DEVICE)  # shape = (N, 3, 160, 160)

    with torch.no_grad():
        embeds = facenet(batch_tensor)  # shape = (N, 512)
    embeds_cpu = embeds.cpu().numpy()  # (N, 512)
    return embeds_cpu.tolist()


@app.post("/bounding_boxes")
async def bounding_boxes(
    image: UploadFile = File(...),
    padding: Optional[int] = Form(None),
):
    """
    1) Load the uploaded image (PIL).
    2) Run YOLO → list of [x1, y1, x2, y2].
    3) Optionally add padding to the bottom-right corner.
    """
    pil_img = pil_from_uploadfile(image)

    # Run YOLO in background thread so we don’t block the event loop
    loop = asyncio.get_event_loop()
    raw_boxes: List[List[float]] = await loop.run_in_executor(
        None,
        _sync_yolo_inference,
        pil_img
    )

    if padding is not None:
        padded: List[List[float]] = []
        for box in raw_boxes:
            x1, y1, x2, y2 = box
            padded.append([x1, y1, x2 + padding, y2 + padding])
        raw_boxes = padded

    return {"boxes": raw_boxes}


@app.post("/crop_images")
async def crop_images(
    image: UploadFile = File(...),
    boxes: List[List[float]] = Form(...),
):
    """
    1) Load PIL image from upload.
    2) For each [x1,y1,x2,y2], crop and base64-encode to JPEG.
    3) Return list of base64 strings.
    """
    pil_img = pil_from_uploadfile(image)
    cropped_b64_list: List[str] = []

    for (x1, y1, x2, y2) in boxes:
        crop = pil_img.crop((x1, y1, x2, y2))
        buf = io.BytesIO()
        crop.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        cropped_b64_list.append(b64)

    return {"images": cropped_b64_list}


@app.post("/vectorize_face", response_model=VectorFaceResponse)
async def vectorize_face(
    face: UploadFile = File(...),
):
    """
    1) Load single face as PIL.
    2) Transform → tensor(1,3,160,160), move to DEVICE.
    3) Run facenet → return 1×512 vector as list.
    """
    pil_face = pil_from_uploadfile(face)
    face_tensor = _transform(pil_face).unsqueeze(0).to(DEVICE)

    # Run Facenet in a threadpool so we don’t block event loop
    loop = asyncio.get_event_loop()
    def _single_infer(tensor):
        with torch.no_grad():
            e = facenet(tensor)  # shape (1, 512)
        return e.cpu().numpy().squeeze().tolist()

    vec: List[float] = await loop.run_in_executor(
        None,
        _single_infer,
        face_tensor
    )
    return {"vector": vec}


@app.post("/vectorize_faces", response_model=VectorFacesResponse)
async def vectorize_faces(
    image: UploadFile = File(...),
    padding: Optional[int] = Form(None),
):
    """
    1) Load the uploaded image.
    2) Detect with YOLO (in executor).
    3) Apply optional padding → get final boxes.
    4) Crop all faces into a Python list of PIL.
    5) Batch‐run them through FaceNet (in executor) → list of [512]-vectors.
    """
    pil_img = pil_from_uploadfile(image)

    # (2) Run YOLO in executor
    loop = asyncio.get_event_loop()
    raw_boxes: List[List[float]] = await loop.run_in_executor(
        None,
        _sync_yolo_inference,
        pil_img
    )

    # (3) Apply padding if requested
    if padding is not None:
        padded: List[List[float]] = []
        for box in raw_boxes:
            x1, y1, x2, y2 = box
            padded.append([x1, y1, x2 + padding, y2 + padding])
        raw_boxes = padded

    # (4) Crop all face regions into PIL list
    face_crops: List[Image.Image] = []
    for (x1, y1, x2, y2) in raw_boxes:
        crop = pil_img.crop((x1, y1, x2, y2))
        face_crops.append(crop)

    # (5) Batch‐run FaceNet (in executor)
    batch_embeddings: List[List[float]] = await loop.run_in_executor(
        None,
        _sync_facenet_batch,
        face_crops
    )

    return {"vectors": batch_embeddings}


# ─── If run as a script, launch Uvicorn with multiple workers ─────────────────────
if __name__ == "__main__":
    import multiprocessing
    import uvicorn

    # Number of logical CPUs; you can reduce this if you run out of GPU VRAM.
    num_workers = multiprocessing.cpu_count()

    uvicorn.run(
        "yoloservice:app",
        host="0.0.0.0",
        port=8000,
        workers=num_workers,
        reload=False  # Set True only if you want auto-reload in dev (not with >1 worker)
    )
