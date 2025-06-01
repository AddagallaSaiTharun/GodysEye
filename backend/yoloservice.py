import io
import base64
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

# Load models once at startup
yolo = YOLO(config.MODEL_PATH)
facenet = InceptionResnetV1(pretrained="vggface2").eval()
_transform = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])

class BoxesRequest(BaseModel):
    padding: Optional[int] = None

class CropRequest(BaseModel):
    # boxes come as a list of [x1, y1, x2, y2]
    boxes: List[List[float]]

class VectorFaceResponse(BaseModel):
    vector: List[float]

class VectorFacesResponse(BaseModel):
    vectors: List[List[float]]


def pil_from_uploadfile(file: UploadFile) -> Image.Image:
    """Read an UploadFile into a PIL Image."""
    contents = file.file.read()
    return Image.open(io.BytesIO(contents)).convert("RGB")


@app.post("/bounding_boxes")
async def bounding_boxes(
    image: UploadFile = File(...),
    padding: Optional[int] = Form(None),
):
    """
    Detect face bounding boxes with YOLO. Returns a list of [x1, y1, x2, y2].
    If `padding` is provided, x2 and y2 are increased by padding.
    """
    img = pil_from_uploadfile(image)
    results = yolo(img)
    # results[0].boxes.xyxy is a torch.Tensor of shape (N, 4)
    raw_boxes = results[0].boxes.xyxy.cpu().numpy().tolist()

    if padding is not None:
        padded = []
        for box in raw_boxes:
            x1, y1, x2, y2 = box
            # Only apply padding to x2,y2 (indices 2 and 3):
            padded.append([x1, y1, x2 + padding, y2 + padding])
        raw_boxes = padded

    return {"boxes": raw_boxes}


@app.post("/crop_images")
async def crop_images(
    image: UploadFile = File(...),
    boxes: List[List[float]] = Form(...),
):
    """
    Crop sub-images according to the provided `boxes`.
    Returns a list of base64-encoded JPEG strings (one per box).
    """
    img = pil_from_uploadfile(image)
    cropped_b64_list: List[str] = []

    for (x1, y1, x2, y2) in boxes:
        crop = img.crop((x1, y1, x2, y2))
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
    Takes a single face image (JPEG/PNG), resizes + normalizes via the same transform,
    then returns a 512-dim embedding as a Python list.
    """
    img = pil_from_uploadfile(face)
    img_tensor = _transform(img).unsqueeze(0)  # shape (1, 3, 160, 160)
    with torch.no_grad():
        embed = facenet(img_tensor)  # shape (1, 512)
    vec = embed.cpu().numpy().squeeze().tolist()
    return {"vector": vec}


@app.post("/vectorize_faces", response_model=VectorFacesResponse)
async def vectorize_faces(
    image: UploadFile = File(...),
    padding: Optional[int] = Form(None),
):
    """
    1) Run YOLO to get bounding boxes (with optional padding).
    2) Crop each face.
    3) Vectorize each face via facenet.
    4) Return a list of embeddings.
    """
    img = pil_from_uploadfile(image)
    results = yolo(img)
    raw_boxes = results[0].boxes.xyxy.cpu().numpy().tolist()

    if padding is not None:
        padded = []
        for box in raw_boxes:
            x1, y1, x2, y2 = box
            padded.append([x1, y1, x2 + padding, y2 + padding])
        raw_boxes = padded

    embeddings: List[List[float]] = []
    for (x1, y1, x2, y2) in raw_boxes:
        crop = img.crop((x1, y1, x2, y2))
        tensor = _transform(crop).unsqueeze(0)
        with torch.no_grad():
            embed = facenet(tensor)
        embeddings.append(embed.cpu().numpy().squeeze().tolist())

    return {"vectors": embeddings}


if __name__ == "__main__":
    import multiprocessing
    import uvicorn

    num_workers = multiprocessing.cpu_count()  # or set manually
    uvicorn.run(
        "yoloservice:app",
        host="0.0.0.0",
        port=config.YOLO_SERVICE_PORT,
        workers=num_workers,
        reload=False  # True only during dev
    )