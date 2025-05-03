import os
import cv2
import uuid
import json
import config
from utilities.logger_config import logger
import os

class Video_FramesStorage:
    cam_id = 0
    def __init__(self, metadata_file="frame_metadata", missing_id=uuid.uuid4()):
        self.MISSING_ID = missing_id
        # self.FRAME_DIR = f"{frame_dir}_{self.MISSING_ID}_cam-{cam_id}"
        self.FRAME_DIR = os.path.join(config.FRAME_DIR,f"cam-{Video_FramesStorage.cam_id}")
        self.METADATA_FILE = os.path.join(metadata_file,f"{metadata_file}_{self.MISSING_ID}.json")
        self.missing = 0
        self.MISSING_DIR = os.path.join(config.MISSING_FRAME_DIR,self.MISSING_ID,f"cam-{Video_FramesStorage.cam_id}")
        os.makedirs(self.FRAME_DIR, exist_ok=True)
        os.makedirs(self.MISSING_DIR, exist_ok=True)
        Video_FramesStorage.cam_id += 1

    def extract_frames(self, video_path, frame_skip=5):
        if not os.path.exists(video_path):
            logger.error(f"Video file {video_path} does not exist.")
            return False

        cap = cv2.VideoCapture(video_path)
        frame_id = 0
        saved_frame_id = 0
        metadata = {}

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Save only every Nth frame
            if frame_id % frame_skip == 0:
                unique_id = str(uuid.uuid4())
                frame_filename = os.path.join(self.FRAME_DIR, f"frame_{saved_frame_id}.jpg")
                cv2.imwrite(frame_filename, frame)
                metadata[saved_frame_id] = {"file": frame_filename, "uuid": unique_id}
                saved_frame_id += 1

            frame_id += 1

        cap.release()

        # Optional: Save metadata (uncomment if you want)
        # with open(self.METADATA_FILE, "w") as f:
        #     json.dump(metadata, f, indent=4)

        logger.info(f"Extracted {saved_frame_id} frames (skipped every {frame_skip} frames) and stored metadata.")
        return True



    def save_frames(self,image = None):
        if image is None:
            print("No image provided.")
            return False
        
        frame_filename = os.path.join(self.MISSING_DIR, f"frame_missing_{self.missing}.jpg")
        print(frame_filename)
        image.save(frame_filename)
        self.missing += 1
        print(f"Saved missing frame : ",self.missing)
        return True
