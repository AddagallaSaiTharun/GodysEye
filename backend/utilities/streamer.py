
import cv2

# class Streamer:
#     def __init__(self, resource):
#         self.resource = resource
#         self.cap = cv2.VideoCapture(self.resource)
#         self.id = 0

#     def get_next(self):
#         grabbed, frame = self.cap.read()
#         if grabbed:
#             self.id += 1
#             frame = frame[..., ::-1]  # Convert BGR to RGB
#             return {"frame_id": self.id, "frame": frame}
#         return None

import os
from PIL import Image

class Streamer:
    def __init__(self, frames_dir=""):
        self.frames_dir = frames_dir
        self.frame_files = sorted([
            os.path.join(self.frames_dir, f) 
            for f in os.listdir(self.frames_dir) 
            if f.endswith(".jpg")
        ])
        self.index = 0

    def get_next(self):
        if self.index < len(self.frame_files):
            frame_path = self.frame_files[self.index]
            image = Image.open(frame_path).convert("RGB")
            self.index += 1
            return {
                "frame_id": self.index,
                "frame_path": frame_path,
                "frame_image": image
            }
        return None
