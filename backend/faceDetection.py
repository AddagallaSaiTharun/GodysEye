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
from app.database_sqlite.models import MissingPersons, MissingPersonsFrame, User
from app.database_sqlite.db import get_db
from app.database_sqlite import engine
from app.database_sqlite.models.all_models import Base
from app.utilities.helper import draw_box, create_access_token
from fastapi.middleware.cors import CORSMiddleware
from app.utilities.logger_config import logger
from datetime import timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database_sqlite.schemas.all_schemas import RegisterUser, LoginUser
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
        face_model = Model()
        face_vector = face_model.vectorize_face(image)

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
        db.commit()
        logger.info("Missing person record stored in database: %s", missing_person_id)

        # Store vector in external vector DB and fetch possible matches
        potential_matches = store_and_search_missing(uuid=missing_person_id, vector=face_vector)
        logger.info("Stored face vector and retrieved %d potential matches", len(potential_matches))

        # Log any frames that matched
        for match in potential_matches:
            frame = MissingPersonsFrame(
                missing_person_id=missing_person_id,
                frame_id=match["frame_id"],
                cam_id=match["cam_id"],
                timestamp=match["timestamp"],
                boxes=match["box"]
            )
            db.merge(frame)
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
    camera_id: str = Query(0, description="Filter by camera ID(default to 0) to retrieve frames from specific camera"),
    frame_id: str = Query(0, description="Filter by Frame ID(default to 0) to retrieve specific frame"),
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

        # Count total frames for the person in this camera
        total_frames = db.query(MissingPersonsFrame).filter_by(
            missing_person_id=missing_person_id,
            cam_id=camera_id
        ).count()

        # Fetch specific frame for the person
        frame = db.query(MissingPersonsFrame).filter_by(
            missing_person_id=missing_person_id,
            cam_id=camera_id,
            frame_id=frame_id
        ).first()

        if not frame:
            logger.warning(f"No frame found for person_id={missing_person_id}, camera_id={camera_id}, frame_id={frame_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Frame not found for given ID and camera."
            )

        # Load and encode registered photo (from database)
        registered_photo_bytes = frame.missing_persons.photo
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
                    "camera_id": frame.cam_id,
                    "missing_person_id": frame.missing_person_id,
                    "frame_image": f"data:image/jpeg;base64,{encoded_frame_image}",
                    "registered_photo": f"data:image/jpeg;base64,{encoded_registered_photo}",
                    "total_frames": total_frames,
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
@app.post("/api/upload_video/")
async def upload_video_only(
    video_file: UploadFile = File(..., description="MP4 video file to be uploaded."),
    user_id: str = Depends(get_current_user)
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
        logger.warning(f"[User: {user_id}] Invalid video format: {video_file.content_type}")
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

        logger.info(f"[User: {user_id}] Video uploaded and saved to: {temp_video_path}")

        # Initialize detection model and extract frames
        detector_model = Model()
        frame_extractor = Video_FramesStorage(detection_model=detector_model)

        logger.info(f"[User: {user_id}] Beginning frame extraction.")
        extraction_success = frame_extractor.extract_frames(temp_video_path)

        if not extraction_success:
            logger.error(f"[User: {user_id}] Frame extraction failed for video: {video_file.filename}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Frame extraction failed."
            )

        logger.info(f"[User: {user_id}] Video processed successfully. Camera ID: {frame_extractor.cam_id}")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Video processed successfully.",
                "camera_id": frame_extractor.cam_id
            }
        )

    except Exception as err:
        logger.exception(f"[User: {user_id}] Error occurred while processing video: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the video. Please try again later."
        )

    finally:
        # Clean up: Remove temporary file and release resources
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.debug(f"Temporary video file removed: {temp_video_path}")

        if detector_model:
            detector_model = None
            logger.debug("Detection model released.")