# import torch
# import numpy as np
# import cv2
# from ultralytics import YOLO
# from facenet_pytorch import InceptionResnetV1
# from torchvision import transforms
# from PIL import Image
# from app.utilities.logger_config import logger

# class Model:
#     def __init__(self, model_path="C:/Users/tharu/OneDrive/Desktop/godseye/backend/yolov11l-face.pt"):
#         self.yolo = YOLO(model_path)
#         self.facenet = InceptionResnetV1(pretrained='vggface2').eval()
#         self.transform = transforms.Compose([
#             transforms.Resize((160, 160)),
#             transforms.ToTensor(),
#             transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
#         ])

#     def _get_results(self, image: Image, show=False):
#         results = self.yolo(image)
#         if show:
#             for result in results:
#                 result.show()
#         return results

#     def bounding_boxes(self, image: Image,padding=None):
#         results = self._get_results(image)
#         boxes = results[0].boxes.xyxy.cpu().numpy().tolist()
#         if padding:
#             boxes = [[x + padding if i>=2 else x for i,x in enumerate(box)] for box in boxes]
#         return boxes

#     def crop_images(self, image: Image, boxes):
#         cropped_images = []
#         for (x1, y1, x2, y2) in boxes:
#             cropped_image = image.crop((x1, y1, x2, y2))
#             cropped_images.append(cropped_image)
#         return cropped_images

#     def vectorize_face(self, image: Image):
#         image_tensor = self.transform(image).unsqueeze(0)
#         with torch.no_grad():
#             embedding = self.facenet(image_tensor)
#         return embedding.numpy().squeeze().tolist()

#     def vectorize_faces(self, image: Image,padding=None):
#         faces = self.crop_images(image, self.bounding_boxes(image,padding=padding))
#         vectors = [self.vectorize_face(face) for face in faces]
#         # return np.array(vectors)
#         logger.debug(f"Length of Vecs : {len(vectors)}")
#         return vectors


# client_model.py

import io
import base64
from typing import List, Optional

import numpy as np 
import cv2
import json         

import httpx
from PIL import Image
from app.utilities.logger_config import logger
from app.utilities import config

class Model:
    def __init__(self, base_url: str = f"http://localhost:{config.YOLO_SERVICE_PORT}"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient()

    # async def _image_to_bytes(self, image: Image.Image) -> bytes:
    #     buf = io.BytesIO()
    #     image.save(buf, format="JPEG")
    #     return buf.getvalue()

    async def _image_to_bytes(self, image: Image.Image) -> bytes:
        # 1) Convert PIL→NumPy (H×W×3 in RGB)
        arr = np.array(image.convert("RGB")) # just changing to rgb cuz could be png/rgba 

        # 2) Convert RGB→BGR (cv2 expects BGR)
        bgr = arr[:, :, ::-1]

        # 3) Encode to JPEG in memory
        success, jpeg_buf = cv2.imencode(".jpg", bgr)
        if not success:
            raise RuntimeError("Failed to JPEG‐encode image via OpenCV")

        # 4) Return raw bytes
        return jpeg_buf.tobytes()


    async def bounding_boxes(
        self,
        image: Image.Image,
        padding: Optional[int] = None
    ) -> List[List[float]]:
        """
        Calls POST /bounding_boxes with multipart-form:
          - image: JPEG bytes
          - padding: optional int
        Returns a list of [x1, y1, x2, y2].
        """
        img_bytes = await self._image_to_bytes(image)
        files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
        data = {}
        if padding is not None:
            data["padding"] = str(padding)

        resp = await self._client.post(
            f"{self.base_url}/bounding_boxes",
            files=files,
            data=data
        )
        resp.raise_for_status()
        payload = resp.json()
        return payload["boxes"]

    async def crop_images(
        self,
        image: Image.Image,
        boxes: List[List[float]]
    ) -> List[Image.Image]:
        """
        Calls POST /crop_images with multipart-form:
          - image: JPEG bytes
          - boxes: as JSON‐serialized string in form‐field
        Returns a list of PIL Images.
        """
        img_bytes = await self._image_to_bytes(image)
        # HTTP form: 'boxes' must be a JSON string
        boxes_str = json.dumps(boxes)

        files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
        data = {"boxes": boxes_str}

        resp = await self._client.post(
            f"{self.base_url}/crop_images",
            files=files,
            data=data
        )
        resp.raise_for_status()
        payload = resp.json()
        cropped_b64_list = payload["images"]

        pil_crops: List[Image.Image] = []
        for b64str in cropped_b64_list:
            img_data = base64.b64decode(b64str)
            pil_crops.append(Image.open(io.BytesIO(img_data)).convert("RGB"))
        return pil_crops

    async def vectorize_face(
        self,
        image: Image.Image
    ) -> List[float]:
        """
        Calls POST /vectorize_face with multipart-form:
          - face: JPEG bytes
        Returns a 512‐d float vector.
        """
        img_bytes = await self._image_to_bytes(image)
        files = {"face": ("face.jpg", img_bytes, "image/jpeg")}

        resp = await self._client.post(
            f"{self.base_url}/vectorize_face",
            files=files
        )
        resp.raise_for_status()
        payload = resp.json()
        return payload["vector"]

    async def vectorize_faces(
        self,
        image: Image.Image,
        padding: Optional[int] = None
    ) -> List[List[float]]:
        """
        Calls POST /vectorize_faces with multipart-form:
          - image: JPEG bytes
          - padding: optional int (sent as form field)
        Returns a list of 512‐d vectors, one per detected face.
        """
        img_bytes = await self._image_to_bytes(image)
        files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
        data = {}
        if padding is not None:
            data["padding"] = str(padding)

        resp = await self._client.post(
            f"{self.base_url}/vectorize_faces",
            files=files,
            data=data
        )
        resp.raise_for_status()
        payload = resp.json()
        vectors = payload["vectors"]
        boxes = payload["boxes"]
        logger.debug(f"Received {len(vectors)} face vectors and {len(boxes)} boxes")
        return vectors, boxes

    async def close(self):
        """Close the underlying HTTPX client."""
        await self._client.aclose()