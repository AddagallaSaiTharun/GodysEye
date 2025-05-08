from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from passlib.hash import argon2
import uuid
from PIL import Image
from fastapi.responses import JSONResponse
import os
import io
import base64
import numpy as np
import shutil
from app.utilities.frames_storage import Video_FramesStorage
from app.utilities.validation import get_current_user 
from app.utilities.yolo_facenet import Model
from app.utilities import config
from app.database_sqlite.models.all_models import MissingPersons, MissingPersonsFrame, User, Base
from app.database_sqlite.schemas.all_schemas import RegisterUser, LoginUser
from app.database_sqlite.db import get_db,engine
from app.utilities.helper import draw_box, create_access_token
from fastapi.middleware.cors import CORSMiddleware
from app.utilities.logger_config import logger
from datetime import timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.utilities.vector_storage import store_and_search_missing




# Create tables only if they don't exist
Base.metadata.create_all(bind=engine)

# Your main logic starts below
logger.info("Database and tables are ready.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Application Started")

############################
# Authentication Endpoints
############################

# Sign Up
@app.post("/api/signup", status_code=status.HTTP_201_CREATED)
def register_user(user: RegisterUser, db: Session = Depends(get_db)):
    """
    Register a new user with the application.

    Args:
        user (RegisterUser): Contains first name, last name, email, and password.
        db (Session): SQLAlchemy database session dependency.

    Raises:
        HTTPException: If email already exists (400).
        HTTPException: If database error occurs (500).
        HTTPException: If unexpected error occurs (500).

    Returns:
        dict: Success message.
    """
    logger.info("Attempting to register user with email: %s", user.email)

    try:
        # Check if the user with the given email already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.warning("Registration failed. Email already exists: %s", user.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists."
            )

        # Hash the user password securely
        hashed_password = argon2.hash(user.password)

        # Create a new User instance
        new_user = User(
            user_id=str(uuid.uuid4()),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=hashed_password
        )

        # Save the new user to the database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info("User registered successfully: %s", new_user.email)
        return {"message": "User registered successfully."}

    except SQLAlchemyError as db_err:
        logger.error("Database error during user registration: %s", db_err)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(db_err)}"
        )

    except Exception as e:
        logger.exception("Unexpected error during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

# Sign In
@app.post("/api/signin", status_code=status.HTTP_200_OK)
def login_user(login_data: LoginUser, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token upon successful login.

    Args:
        login_data (LoginUser): Contains user's email and password.
        db (Session): SQLAlchemy database session dependency.

    Raises:
        HTTPException: If user is not found (401).
        HTTPException: If password is incorrect (401).
        HTTPException: For any unexpected server errors (500).

    Returns:
        dict: Contains success message, access token, token type, and user information.
    """

    try:
        logger.info("Attempting to login user with email: %s", login_data.email)
        # Retrieve user from database using email
        user_in_db = db.query(User).filter(User.email == login_data.email).first()

        if not user_in_db:
            logger.warning(f"Login failed: User with email {login_data.email} not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify provided password against hashed password
        if not argon2.verify(login_data.password, user_in_db.password_hash):
            logger.warning(f"Login failed: Incorrect password for email {login_data.email}.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Create JWT token
        token_payload = {
            "sub": user_in_db.email,
            "user_id": user_in_db.user_id
        }
        access_token = create_access_token(
            data=token_payload,
            expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"User {user_in_db.email} logged in successfully.")

        # Return successful response
        return {
            "message": "User signed in successfully",
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "first_name": user_in_db.first_name,
                "last_name": user_in_db.last_name,
                "email": user_in_db.email
            }
        }

    except Exception as err:
        logger.error(f"Unexpected error during login for email {login_data.email}: {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(err)}"
        )


############################
# Frontend Endpoints
############################

# Mount static files (CSS, JS, etc.) from Vue's build output
app.mount("/static", StaticFiles(directory=config.VUE_DIST_DIR, html=True), name="static")

# Root route to serve index.html for SPA
@app.get("/", response_class=FileResponse, status_code=status.HTTP_200_OK)
async def serve_vue_app():
    """
    Serve the main entry point of the Vue.js application.
    This route handles the root path and delivers the SPA's index.html file.
    """
    INDEX_HTML_PATH = os.path.join(config.VUE_DIST_DIR, "index.html")
    if not os.path.exists(INDEX_HTML_PATH):
        logger.error(f"Vue frontend entry point not found at {INDEX_HTML_PATH}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frontend is currently unavailable. Please try again later."
        )

    logger.info(f"Serving Vue frontend from {INDEX_HTML_PATH}")
    return FileResponse(INDEX_HTML_PATH, media_type="text/html")


############################
# Missing Person Endpoints
############################

# Register a missing person
@app.post("/api/register_missing_person", status_code=status.HTTP_201_CREATED)
async def register_missing_person(
    user_id: str = Depends(get_current_user),  # Authenticated user ID
    first_name: str = Form(...),
    last_name: str = Form(...),
    details: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Register a new missing person in the database.

    Args:
        user_id (str): Authenticated user's ID (auto-injected via Depends).
        first_name (str): First name of the missing person.
        last_name (str): Last name of the missing person.
        details (str): Additional details about the missing person.
        photo (UploadFile): Image file of the missing person.
        db (Session): SQLAlchemy session for DB interaction.

    Raises:
        HTTPException: If no face is detected in the image (400).
        HTTPException: For general database or processing errors (500).

    Returns:
        dict: A success message with the missing person ID.
    """
    try:
        logger.info("Starting registration process for missing person by user %s", user_id)

        # Load and convert the uploaded image to RGB JPEG
        image = Image.open(io.BytesIO(await photo.read())).convert("RGB")
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="JPEG")
        jpeg_bytes = image_buffer.getvalue()

        # Generate unique ID and extract face vector
        missing_person_id = str(uuid.uuid4())
        face_model = Model(config.MODEL_PATH)
        face_vector = face_model.vectorize_faces(image)[0]
        logger.info(f"Face vector: {face_vector}")

        if face_vector is None:
            logger.warning("Face not detected in uploaded image by user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in the uploaded photo."
            )

        # Create and store missing person record
        missing_person = MissingPersons(
            missing_person_id=missing_person_id,
            first_name=first_name,
            last_name=last_name,
            details=details,
            photo=jpeg_bytes
        )
        db.add(missing_person)
        logger.info("Missing person record stored in database: %s", missing_person_id)

        # Store vector in external vector DB and fetch possible matches
        potential_matches = store_and_search_missing(person_id=missing_person_id, query_vector=face_vector,max_distance=0.75)
        logger.info(f"Stored face vector and retrieved {len(potential_matches)} potential matches")
        d = {}
        for match in potential_matches:
            cam_id = match['cam_id']

            d[cam_id] = d.get(cam_id, 0)
            missing_frame_id = d[cam_id]

            logger.info(f"cam_id : {match['cam_id']}, frame_id: {match['frame_id']}, missing_frame_id: {d[match['cam_id']]}")
            frame = MissingPersonsFrame(
                missing_person_id=missing_person_id,
                missing_frame_id=missing_frame_id,
                frame_id=match["frame_id"],
                cam_id=match["cam_id"],
                timestamp=match["timestamp"],
                box=match["box"],
                score=match['score']
            )
            d[cam_id] += 1
            db.add(frame)
        db.commit()

        logger.info("Missing person registration completed successfully for ID: %s", missing_person_id)

        return {
            "status": "success",
            "message": "Missing person registered successfully.",
            "missing_person_id": missing_person_id
        }

    except Exception as ex:
        logger.exception("Unexpected error occurred during missing person registration.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(ex)}"
        )
 
# Get missing person frame
@app.get("/api/missing_person_frame", status_code=status.HTTP_200_OK)
async def get_missing_person_frame(
    user_id: str = Depends(get_current_user),
    missing_person_id: str = Query(None, description="filter by Missing person ID to retrieve frames"),
    camera_id: str = Query(None, description="Filter by camera ID(default to 0) to retrieve frames from specific camera"),
    frame_id: str = Query("0", description="Filter by Frame ID(default to frame_0) to retrieve specific frame"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    start_timestamp: str = Query(None),
    end_timestamp: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieves a specific frame related to a missing person from a given camera.

    - If `missing_person_id` is not provided, returns a list of all missing persons.
    - If `missing_person_id` is provided along with camera and frame IDs, it returns the corresponding frame,
      the registered photo, and total frames found for that person in the camera.

    Args:
        user_id (str): Authenticated user ID from JWT.
        missing_person_id (str): ID of the missing person to retrieve frames for.
        camera_id (str): ID of the camera where frames were recorded.
        frame_id (str): Specific frame ID to retrieve.
        start_date (str): (Optional) Filter by start date.
        end_date (str): (Optional) Filter by end date.
        start_timestamp (str): (Optional) Filter by start timestamp.
        end_timestamp (str): (Optional) Filter by end timestamp.
        db (Session): SQLAlchemy DB session.

    Returns:
        JSON response with frame data or list of missing persons.
    """
    try:
        # Case: No specific person ID provided — return list of all missing persons
        if missing_person_id is None:
            logger.info("Fetching all missing persons.")
            persons = db.query(MissingPersons).all()
            result = [
                {
                    "id": person.missing_person_id,
                    "first_name": person.first_name,
                    "last_name" : person.last_name,
                    "name": f"{person.first_name}, {person.last_name}",
                    "details": person.details
                }
                for person in persons
            ]
            logger.info("Returning missing persons list and camera names.")
            return JSONResponse(
                content={"persons": result},
                status_code=status.HTTP_200_OK
            )

        camera_ids = db.query(MissingPersonsFrame.cam_id)\
            .filter_by(missing_person_id=missing_person_id)\
            .distinct()\
            .all()
        camera_ids = [cam_id[0] for cam_id in camera_ids]

        if not camera_ids:
            logger.warning(f"No cameras found for person_id={missing_person_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cameras found for given ID."
            )

        if not camera_id:
            logger.info("Returning missing persons list and camera names.")
            camera_id = camera_ids[0] if camera_ids else None

        logger.info(f"cameras_ids: {camera_ids}, current_cam: {camera_id}")

        # Count total frames for the person in this camera
        total_frames = db.query(MissingPersonsFrame).filter_by(
            missing_person_id=missing_person_id,
            cam_id=camera_id
        ).count()

        # Fetch specific frame for the person
        frame = db.query(MissingPersonsFrame).filter_by(
            missing_person_id=missing_person_id,
            cam_id=camera_id,
            missing_frame_id=frame_id
        ).first()

        if not frame:
            logger.warning(f"No frame found for person_id={missing_person_id}, camera_id={camera_id}, missing_frame_id={frame_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Frame not found for given ID and camera."
            )

        # Load and encode registered photo (from database)
        registered_photo_bytes = frame.missing_person.photo
        registered_image = Image.open(io.BytesIO(registered_photo_bytes))
        buffer_registered = io.BytesIO()
        registered_image.save(buffer_registered, format="JPEG")
        buffer_registered.seek(0)
        encoded_registered_photo = base64.b64encode(buffer_registered.read()).decode("utf-8")

        # Build path to saved frame image
        frame_image_path = os.path.join(config.FRAME_DIR, frame.cam_id, f"{frame.frame_id}.jpeg")
        if not os.path.exists(frame_image_path):
            logger.error(f"Frame image not found on disk at {frame_image_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Frame image file not found on disk."
            )

        # Annotate and encode frame image
        image = Image.open(frame_image_path).convert("RGB")
        np_image = np.array(image)

        if frame.box:
            np_image = draw_box(np_image, frame.box)

        image_with_boxes = Image.fromarray(np_image)
        buffer_frame = io.BytesIO()
        image_with_boxes.save(buffer_frame, format="JPEG")
        buffer_frame.seek(0)
        encoded_frame_image = base64.b64encode(buffer_frame.read()).decode("utf-8")

        logger.info(f"Successfully returned frame for missing_person_id={missing_person_id}, frame_id={frame_id}")
        return JSONResponse(
            content={
                "message": "Frame data retrieved successfully.",
                "data": {
                    "frame_id": frame.frame_id,
                    "present_camera": frame.cam_id,
                    "missing_person_id": frame.missing_person_id,
                    "frame_image": f"data:image/jpeg;base64,{encoded_frame_image}",
                    "registered_photo": f"data:image/jpeg;base64,{encoded_registered_photo}",
                    "total_frames": total_frames - 1,
                    "camera_names": camera_ids
                }
            },
            status_code=status.HTTP_200_OK
        )

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        logger.exception("Unexpected error while retrieving missing person frame.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later."
        )


############################
# Video Streaming Endpoint
############################

# Upload video for processing
@app.post("/api/upload_video",status_code=status.HTTP_201_CREATED)
async def upload_video_only(
    user_id: str = Depends(get_current_user),
    video_file: UploadFile = File(..., description="MP4 video file to be uploaded."),
    frame_skip:int = Form(..., description="Number of frames to skip between extractions")
):
    """
    Upload and process an MP4 video to extract frames for facial recognition.

    This endpoint allows an authenticated user to upload a video file (only `.mp4` format supported),
    stores it temporarily, extracts frames using a detection model, and then deletes the file after processing.

    Args:
        video_file (UploadFile): The video file uploaded by the user.
        user_id (str): Authenticated user ID extracted from JWT.

    Returns:
        JSONResponse: A success message with the associated camera ID on successful processing,
                      or an error message with the appropriate status code.
    """
    # Validate video file type
    if video_file.content_type != "video/mp4":
        logger.warning(f" Invalid video format: {video_file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only MP4 videos are accepted."
        )

    temp_video_dir = config.UPLOAD_DIR
    os.makedirs(temp_video_dir, exist_ok=True)

    temp_video_path = os.path.join(temp_video_dir, video_file.filename)

    detector_model = None
    try:
        # Save uploaded video to temporary path
        with open(temp_video_path, "wb") as output_file:
            shutil.copyfileobj(video_file.file, output_file)

        logger.info(f"Video uploaded and saved to: {temp_video_path}")

        # Initialize detection model and extract frames
        detector_model = Model(config.MODEL_PATH)
        frame_extractor = Video_FramesStorage(detection_model=detector_model)

        logger.info(f"Beginning frame extraction.")
        extraction_success = frame_extractor.extract_frames(temp_video_path,frame_skip)

        if not extraction_success:
            logger.error(f"Frame extraction failed for video: {video_file.filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Frame extraction failed."
            )

        logger.info(f"Video processed successfully. Camera ID: {frame_extractor.cam_id}")
        return {
            "message": "Video processed successfully.",
            "camera_id": frame_extractor.cam_id
        }

    except Exception as err:
        logger.exception(f"Error occurred while processing video: {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(err)}"
        )

    finally:
        if detector_model:
            detector_model = None
            logger.debug("Detection model released.")