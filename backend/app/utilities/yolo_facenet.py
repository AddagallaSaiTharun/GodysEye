import torch
import numpy as np
import cv2
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
from torchvision import transforms
from PIL import Image
from app.utilities.logger_config import logger

class Model:
    def __init__(self, model_path="C:/Users/tharu/OneDrive/Desktop/godseye/backend/yolov11l-face.pt"):
        self.yolo = YOLO(model_path)
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval()
        self.transform = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def _get_results(self, image: Image, show=False):
        results = self.yolo(image)
        if show:
            for result in results:
                result.show()
        return results

    def bounding_boxes(self, image: Image,padding=None):
        results = self._get_results(image)
        boxes = results[0].boxes.xyxy.cpu().numpy().tolist()
        if padding:
            boxes = [[x + padding if i>=2 else x for i,x in enumerate(box)] for box in boxes]
        return boxes

    def crop_images(self, image: Image, boxes):
        cropped_images = []
        for (x1, y1, x2, y2) in boxes:
            cropped_image = image.crop((x1, y1, x2, y2))
            cropped_images.append(cropped_image)
        return cropped_images

    def vectorize_face(self, image: Image):
        image_tensor = self.transform(image).unsqueeze(0)
        with torch.no_grad():
            embedding = self.facenet(image_tensor)
        return embedding.numpy().squeeze().tolist()

    def vectorize_faces(self, image: Image,padding=None):
        faces = self.crop_images(image, self.bounding_boxes(image,padding=padding))
        vectors = [self.vectorize_face(face) for face in faces]
        # return np.array(vectors)
        logger.debug(f"Length of Vecs : {len(vectors)}")
        return vectors