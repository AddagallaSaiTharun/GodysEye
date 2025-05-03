import base64
from typing import Optional
import cv2
from dataHandlers.MissingPersonHandler import add_to_db,get_from_db
from fastapi import FastAPI, Query, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utilities.yolo_facenet import Model
from utilities.streamer import Streamer
import numpy as np
from numpy import dot
from numpy.linalg import norm
from PIL import Image
import io
import os
import shutil
import uuid
from utilities.frames_storage import Video_FramesStorage
from fastapi.responses import JSONResponse
from jose import jwt
import config
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from argon2 import PasswordHasher
from utilities.validation import get_current_user
import uuid
from datetime import datetime, timedelta
from dataHandlers.UsersHandler import load_users, save_users
from utilities.logger_config import logger

os.makedirs(config.UPLOAD_DIR, exist_ok=True)
os.makedirs(f"{config.REGISTERD_PHOTO_DIR}", exist_ok=True)

class StartStream(BaseModel):
    frames_dir: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# File storage
USERS_FILE = "database/Users.json"

# Models
class RegisterUser(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str

# Argon2 hasher
ph = PasswordHasher()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)

logger.info("Application Started")
# Sign Up
@app.post("/signup")
def register(user: RegisterUser):
    users = load_users(USERS_FILE)

    if any(u["email"] == user.email for u in users):
        raise HTTPException(status_code=400, detail="Email already exists.")

    hashed_password = ph.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["id"] = str(uuid.uuid4())

    users.append(user_dict)
    save_users(users,USERS_FILE)

    return JSONResponse(content={"message": "User registered successfully"},status_code=201)

# Sign In
@app.post("/signin")
def login(user: LoginUser):
    users = load_users(USERS_FILE)
    db_user = next((u for u in users if u["email"] == user.email), None)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        ph.verify(db_user["password"], user.password)
    except:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {"sub": user.email,"user_id":db_user["id"]}
    access_token = create_access_token(token_data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {
        "message": "Login successful",
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "first_name": db_user["first_name"],
            "last_name": db_user["last_name"],
            "email": db_user["email"]
        },
    }




app.mount("/static", StaticFiles(directory="./dist", html=True), name="static")

# Initialize Model
model = Model("yolov11n-face.pt")

class StreamRequest(BaseModel):
    flag: str

streamers = {}
 
missing = {}




@app.get("/", response_class=FileResponse)
async def serve_vue_app():
    return FileResponse("dist/index.html")
    

@app.post("/detect_faces/")
async def detect_faces(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    boxes = model.bounding_boxes(image)
    return JSONResponse(content = {"data":{"bounding_boxes": boxes}},status_code=200)

@app.post("/vectorize_faces/")
async def vectorize_faces(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    vectors = model.vectorize_faces(image)
    return JSONResponse(content = {"data":{"vectors": vectors}},status_code=200)


def cosine_similarity(vec1, vec2):
        """
        Computes cosine similarity between two vectors.
        """
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

@app.post("/start_stream/")
async def start_stream(
    user_id: str = Depends(get_current_user),
    ):
    frames_dir = "video_frames" + "_" + user_id
    if frames_dir not in streamers:
        streamers[frames_dir] = Streamer(frames_dir)
    return JSONResponse(content = {"message": f"Streaming started for directory: {frames_dir}"},status_code=200)

@app.get("/persons")
async def stream_frame(
    user_id: str = Depends(get_current_user),
    id: str = Query(None, description="Filter by uuid"),
    start_date: str = Query(None, description="Filter by start_date"),
    start_timestamp: str = Query(None, description="Filter by start_date"),
    end_date: str = Query(None, description="Filter by end_date"),
    end_timestamp: str = Query(None, description="Filter by start_date"),
    cam_id: str = Query(None, description="Filter by end_date"),
    frame_id: str = Query(None, description="Filter by frame_id"),
    ):
    if not id:
        data = get_from_db()
        return JSONResponse(content=data,status_code=200)
    missing_person_frame_dir = os.path.join(config.MISSING_FRAME_DIR,id)
    if not os.path.exists(missing_person_frame_dir):
        return JSONResponse(content=[], status_code=200)
    cam_folder_name = os.listdir(missing_person_frame_dir)[0] if not cam_id else os.path.join(missing_person_frame_dir, cam_id)
    cam_path = os.path.join(missing_person_frame_dir, cam_folder_name)
    if os.path.isdir(cam_path):
        registerd_path = f"{config.REGISTERD_PHOTO_DIR}/{id}.jpeg"
        frame_path = os.path.join(cam_path, f"frame_missing_{ frame_id }.jpg") 
        image = Image.open(frame_path).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        encoded_image_missing = base64.b64encode(buffer.read()).decode("utf-8")

        image = Image.open(registerd_path).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        encoded_image_registered = base64.b64encode(buffer.read()).decode("utf-8")


        return JSONResponse(content={"message":"Frames fetched successfully.","data":{
            "frame_id": frame_id,
            "frame_path": frame_path,
            "frame_image": f'data:image/jpeg;base64,{encoded_image_missing}',
            "camera_names":os.listdir(missing_person_frame_dir),
            "present_camera":cam_folder_name,
            "registered_photo":f'data:image/jpeg;base64,{encoded_image_registered}',
            "total_frames":len(os.listdir(cam_path))
        }},status_code=200)

def draw_boxes(image: np.ndarray, boxes: list, color=(255, 0, 0), thickness=6):
    if isinstance(image, Image.Image):
        image = np.array(image)
    for box in boxes:
        # print(box)
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        # cropped_image = image.crop((x1, y1, x2, y2))
    return image

@app.post("/missing_persons/")
async def upload_video(
    user_id: str = Depends(get_current_user),
    first_name: str = Form(...),
    last_name: str = Form(...),
    details: str = Form(...),
    photo: UploadFile = File(...),
    video: Optional[UploadFile] = File(None)
):
    photo.file.seek(0)
    pil_img = Image.open(photo.file).convert("RGB")
    missing_vector = model.vectorize_face(pil_img)
    # Step 1: Save missing person details to DB
    missing_id = add_to_db(created_by=user_id, first_name=first_name, last_name=last_name, details=details,vector=missing_vector)
    pil_img.save(f"{config.REGISTERD_PHOTO_DIR}/{missing_id}.jpeg",format="JPEG")
    # Save uploaded video
    filename = f"video_{missing_id}.mp4"
    file_path = os.path.join(config.UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # Step 2: Extract frames and metadata
    video_framesstorage = Video_FramesStorage(missing_id = missing_id)
    flag = video_framesstorage.extract_frames(file_path)
    # Step 3: Delete video file after processing
    os.remove(file_path)
    logger.info("Calling process video function")
    process_video(missing_id,missing_vector,video_framesstorage)

    return JSONResponse(content={
        "message": "Video uploaded, frames extracted, metadata saved, and video deleted.",
    }, status_code=200)

def process_video(missing_id,missing_vector,video_frame_storage = None):
    # Step 2: Get next frame
    frames_dir = video_frame_storage.FRAME_DIR
    if frames_dir not in streamers:
        streamers[frames_dir] = Streamer(frames_dir)
    for _ in range(len(streamers[frames_dir].frame_files)):
        frame_data = streamers[frames_dir].get_next()
        if not frame_data:
            return False
        image = frame_data["frame_image"]  # Assuming it's a NumPy array (OpenCV format)

        # Step 3: Face detection and vectorization
        bounding_boxes = model.bounding_boxes(image)
        vectors = model.vectorize_faces(image)
        # print(len(vectors), len(vectors[0]))
        threshold = 0.7
        similar_vecs_indices = []

        for i, vector in enumerate(vectors):
            sim = cosine_similarity(vector[0], missing_vector[0])
            # print(i, sim)
            if sim >= threshold:
                similar_vecs_indices.append(i)

        # Step 4: Get matched boxes
        matching_boxes = [bounding_boxes[i] for i in similar_vecs_indices]
        if matching_boxes:
            image_with_boxes = Image.fromarray(draw_boxes(image.copy(), matching_boxes))
            # image_with_boxes.save(f"./debug/debug{random.randint(0, 1000)}.jpg")
            flag = video_frame_storage.save_frames(image_with_boxes)

    # Step 6: Convert image to base64 for frontend
    # image_base64 = image_to_base64(image_with_boxes)
    streamers[frames_dir] = None
    return True