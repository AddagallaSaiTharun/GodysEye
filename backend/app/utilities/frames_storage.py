import os
import cv2
import uuid
import json
from app.utilities import config
import datetime
from PIL import Image
from app.utilities.logger_config import logger
from app.utilities.vector_storage import store_frame_vectors

class Video_FramesStorage:
    cam_id_counter = 0  # class variable to track camera IDs

    def __init__(self, detection_model=None):
        self.detection_model = detection_model
        self.cam_id = Video_FramesStorage.cam_id_counter
        Video_FramesStorage.cam_id_counter += 1
        self.FRAME_DIR = os.path.join(config.FRAME_DIR, f"cam-{self.cam_id}")
        os.makedirs(self.FRAME_DIR, exist_ok=True)

    async def extract_frames(self, video_path):
        if not os.path.exists(video_path):
            logger.error(f"Video file {video_path} does not exist.")
            return False

        cap = cv2.VideoCapture(video_path)
        frame_id = 0
        fps = cap.get(cv2.CAP_PROP_FPS)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            seconds = frame_id / fps  # in seconds
            timestamp = str(datetime.timedelta(seconds=round(seconds, 3)))  # e.g., "0:00:03.000"

            frame_filename = os.path.join(self.FRAME_DIR, f"frame_{frame_id}.jpeg")

            # Convert OpenCV image (BGR) to PIL image (RGB)
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)

            # Get bounding boxes using YOLO
            boxes = self.detection_model.bounding_boxes(pil_image)
            if boxes:  # if faces are detected
                vectors = self.detection_model.vectorize_faces(pil_image)
                cv2.imwrite(frame_filename, frame)  # Save the frame

                # Call the external function with all required info
                store_frame_vectors(
                    cam_id=f"cam-{self.cam_id}",
                    frame_id=f"frame_{frame_id}",
                    bounding_boxes=boxes,
                    vectors=vectors,
                    timestamp=timestamp
                )

            frame_id += 1

        cap.release()
        logger.info(f"Processed {frame_id} frames.")
        return True




# class Video_FramesStorage:
#     def __init__(self, metadata_file="frame_metadata", missing_id=uuid.uuid4()):
#         cam_id = 0
#         self.MISSING_ID = missing_id
#         # self.FRAME_DIR = f"{frame_dir}_{self.MISSING_ID}_cam-{cam_id}"
#         self.FRAME_DIR = os.path.join(config.FRAME_DIR,f"cam-{cam_id}")
#         self.METADATA_FILE = f"{metadata_file}_{self.MISSING_ID}.json"
#         self.missing = 0
#         self.MISSING_DIR = os.path.join(config.MISSING_FRAME_DIR,self.MISSING_ID,f"cam-{cam_id}")
#         os.makedirs(self.FRAME_DIR, exist_ok=True)
#         os.makedirs(self.MISSING_DIR, exist_ok=True)
#         cam_id += 1

#     def extract_frames(self, video_path):
#         if not os.path.exists(video_path):
#             print(f"Video file {video_path} does not exist.")
#             return False
        
#         cap = cv2.VideoCapture(video_path)
#         frame_id = 0
#         metadata = {}

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             unique_id = str(uuid.uuid4())
#             frame_filename = os.path.join(self.FRAME_DIR, f"frame_{frame_id}.jpg")
#             cv2.imwrite(frame_filename, frame)
#             metadata[frame_id] = {"file": frame_filename, "uuid": unique_id}
#             frame_id += 1

#         cap.release()

#         with open(self.METADATA_FILE, "w") as f:
#             json.dump(metadata, f, indent=4)

#         print(f"Extracted {frame_id} frames and stored metadata.")
#         return True


#     def save_frames(self,image = None):
#         if image is None:
#             print("No image provided.")
#             return False
        
#         frame_filename = os.path.join(self.MISSING_DIR, f"frame_missing_{self.missing}.jpg")
#         cv2.imwrite(frame_filename, image)
#         self.missing += 1
#         print(f"Saved missing frame : ",self.missing)
#         return True
