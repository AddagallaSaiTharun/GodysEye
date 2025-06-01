import os
import cv2
import uuid
import json
from app.utilities import config
import datetime
from PIL import Image
from app.utilities.logger_config import logger
from app.utilities.vector_storage import store_frame_vectors
from uuid import uuid4

class Video_FramesStorage:

    def __init__(self, detection_model=None):
        self.detection_model = detection_model
        self.cam_id = str(uuid4())
        self.FRAME_DIR = os.path.join(config.FRAME_DIR, f"cam-{self.cam_id}")
        os.makedirs(self.FRAME_DIR, exist_ok=True)

    # async def extract_frames(self, video_path,frame_skip=5):
    #     if not os.path.exists(video_path):
    #         logger.error(f"Video file {video_path} does not exist.")
    #         return False

    #     cap = cv2.VideoCapture(video_path)
    #     frame_id = 0
    #     fps = cap.get(cv2.CAP_PROP_FPS)

    #     while cap.isOpened():
    #         ret, frame = cap.read()
    #         if not ret:
    #             break
            
    #         if frame_id % frame_skip != 0:
    #             frame_id += 1
    #             continue
    #         seconds = frame_id / fps  # in seconds
    #         timestamp = str(datetime.timedelta(seconds=round(seconds, 3)))  # e.g., "0:00:03.000"

    #         frame_filename = os.path.join(self.FRAME_DIR, f"frame_{frame_id}.jpeg")

    #         # Convert OpenCV image (BGR) to PIL image (RGB)
    #         image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #         pil_image = Image.fromarray(image_rgb)

    #         # Get bounding boxes using YOLO
    #         # boxes = await self.detection_model.bounding_boxes(pil_image)
    #         # if boxes:  # if faces are detected
    #         vectors, boxes = await self.detection_model.vectorize_faces(pil_image)
    #         if boxes:
    #             cv2.imwrite(frame_filename, frame)  # Save the frame

    #             # Call the external function with all required info
    #             store_frame_vectors(
    #                 cam_id=f"cam-{self.cam_id}",
    #                 frame_id=f"frame_{frame_id}",
    #                 bounding_boxes=boxes,
    #                 vectors=vectors,
    #                 timestamp=timestamp
    #             )

    #         frame_id += 1

    #     cap.release()
    #     logger.info(f"Processed {frame_id} frames.")
    #     try:
    #         os.remove(config.UPLOAD_DIR)
    #         logger.info(f"Removed the video file in path {config.UPLOAD_DIR}")
    #     except Exception as e:
    #         logger.error(f"Error removing video file: {e}")
    #     return True
    async def _vectorize_and_package(
        self,
        frame,
        frame_id: int,
        timestamp: str,
        frame_filename: str,
        padding: Optional[int] = None,
    ) -> dict:
        """
        1) Converts raw OpenCV BGR `frame` → PIL Image (RGB)
        2) Calls `self.detection_model.vectorize_faces(...)`, which now returns (vectors, boxes)
        3) Returns a dict:
            {
               'frame': <the raw BGR frame buffer>,
               'frame_id': <int>,
               'timestamp': <"H:MM:SS.xxx">,
               'frame_filename': <str>,
               'boxes': <List[List[float]]>,
               'vectors': <List[List[float]]>
            }
        """
        try:
            # 1a. Convert BGR → RGB
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)

            # 2. Call vectorize_faces (which must now return (vectors, boxes))
            vectors, boxes = await self.detection_model.vectorize_faces(pil_image, padding=padding)
            return {
                "frame": frame,
                "frame_id": frame_id,
                "timestamp": timestamp,
                "frame_filename": frame_filename,
                "boxes": boxes,
                "vectors": vectors,
            }
        except Exception as e:
            # If something goes wrong (e.g. HTTP error, JSON parsing), we re‐raise so that
            # extract_frames can catch it in its as_completed() loop.
            raise RuntimeError(f"Frame {frame_id} packaging failed: {e}")

    async def _vectorize_with_semaphore(self, semaphore, frame, frame_id, timestamp, frame_filename):
        async with semaphore:
            return await self._vectorize_and_package(
                frame=frame,
                frame_id=frame_id,
                timestamp=timestamp,
                frame_filename=frame_filename,
            )


    # async def extract_frames(self, video_path: str, frame_skip: int = 5) -> bool:
    #     """
    #     1) Opens `video_path` via cv2.VideoCapture.
    #     2) Every `frame_skip`‐th frame is turned into a PIL.Image, then
    #        scheduled as an async task to call `vectorize_faces(...)`.
    #     3) We collect all tasks and use `asyncio.as_completed(...)` to process
    #        them as soon as they finish, writing out JPEGs + calling store_frame_vectors().
    #     """
    #     if not os.path.exists(video_path):
    #         logger.error(f"Video file {video_path} does not exist.")
    #         return False

    #     cap = cv2.VideoCapture(video_path)
    #     fps = cap.get(cv2.CAP_PROP_FPS)
    #     frame_id = 0
    #     tasks = []

    #     semaphore = asyncio.BoundedSemaphore(10)  # Limit concurrency to 10

    #     # 1. Loop through the video, frame by frame. For every frame where
    #     #    frame_id % frame_skip == 0, create a task to vectorize it.
    #     while cap.isOpened():
    #         ret, frame = cap.read()
    #         if not ret:
    #             break

    #         if frame_id % frame_skip == 0:
    #             # Compute timestamp in "H:MM:SS.mmm" format
    #             seconds = frame_id / fps
    #             timestamp = str(datetime.timedelta(seconds=round(seconds, 3)))

    #             # Prepare a filename for saving (if/when we get boxes back)
    #             frame_filename = os.path.join(
    #                 self.FRAME_DIR, f"frame_{frame_id}.jpeg"
    #             )

    #             # Since OpenCV `frame` buffer will be reused on the next read,
    #             # make a copy so we can carry it into the async task:
    #             frame_copy = frame.copy()

    #             # Schedule the async wrapper that calls vectorize_faces + returns metadata:
    #             task = asyncio.create_task(
    #                 self._vectorize_with_semaphore(
    #                     semaphore=semaphore,
    #                     frame=frame_copy,
    #                     frame_id=frame_id,
    #                     timestamp=timestamp,
    #                     frame_filename=frame_filename,
    #                 )
    #             )
    #             tasks.append(task)

    #         frame_id += 1

    #     cap.release()

    #     # 2. As each vectorization finishes, process its result immediately:
    #     for completed_future in asyncio.as_completed(tasks):
    #         try:
    #             # Each item is a dict with keys:
    #             #   'frame', 'frame_id', 'timestamp', 'frame_filename', 'boxes', 'vectors'
    #             result: dict = await completed_future
    #         except Exception as e:
    #             logger.error(f"Error in vectorization task: {e}")
    #             continue

    #         boxes = result["boxes"]
    #         if boxes:
    #             # There was at least one face box → save frame + store vectors
    #             raw_frame = result["frame"]              # still in BGR (OpenCV) format
    #             filename = result["frame_filename"]      # e.g. ".../frame_42.jpeg"
    #             cv2.imwrite(filename, raw_frame)

    #             store_frame_vectors(
    #                 cam_id=f"cam-{self.cam_id}",
    #                 frame_id=f"frame_{result['frame_id']}",
    #                 bounding_boxes=boxes,
    #                 vectors=result["vectors"],
    #                 timestamp=result["timestamp"],
    #             )

    #     logger.info(f"Processed {frame_id} frames (skipping every {frame_skip}).")
    #     # 3. Optionally remove the original upload
    #     try:
    #         os.remove(config.UPLOAD_DIR)
    #         logger.info(f"Removed the video file at {config.UPLOAD_DIR}")
    #     except Exception as e:
    #         logger.error(f"Error removing video file: {e}")

    #     return True

async def extract_frames(self, video_path, frame_skip=5):
    if not os.path.exists(video_path):
        logger.error(f"{video_path} does not exist")
        return False

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_id = 0
    semaphore = asyncio.BoundedSemaphore(10)

    while cap.isOpened():
        # 1. Build one batch of up to BATCH_SIZE tasks
        batch_tasks = []
        for _ in range(config.BATCH_SIZE):
            ret, frame = cap.read()
            if not ret:
                break
            if frame_id % frame_skip == 0:
                seconds = frame_id / fps
                timestamp = str(datetime.timedelta(seconds=round(seconds, 3)))
                frame_filename = os.path.join(self.FRAME_DIR, f"frame_{frame_id}.jpeg")
                frame_copy = frame.copy()

                await semaphore.acquire()
                t = asyncio.create_task(
                    self._vectorize_with_semaphore(
                        semaphore=semaphore,
                        frame=frame_copy,
                        frame_id=frame_id,
                        timestamp=timestamp,
                        frame_filename=frame_filename,
                    )
                )
                batch_tasks.append(t)
            frame_id += 1
        # 2. Process that batch “as they finish”
        for fut in asyncio.as_completed(batch_tasks):
            try:
                result = await fut
            except Exception as e:
                logger.error(f"Error in vectorization task: {e}")
                continue
            if result["boxes"]:
                cv2.imwrite(result["frame_filename"], result["frame"])
                store_frame_vectors(
                    cam_id=f"cam-{self.cam_id}",
                    frame_id=f"frame_{result['frame_id']}",
                    bounding_boxes=result["boxes"],
                    vectors=result["vectors"],
                    timestamp=result["timestamp"],
                )
        # Loop back and build the next batch…

        if not ret:
            break

    cap.release()
    logger.info(f"Processed {frame_id} frames (skipping every {frame_skip}).")
    try:
        os.remove(config.UPLOAD_DIR)
    except Exception as e:
        logger.error(f"Error removing video file: {e}")
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
