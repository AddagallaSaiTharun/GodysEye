import torch
import numpy as np
import cv2
from ultralytics import YOLO
from facenet_pytorch import InceptionResnetV1
from torchvision import transforms
from PIL import Image

class Model:
    def __init__(self, model_path):
        self.yolo = YOLO(model_path)
        self.facenet = InceptionResnetV1(pretrained='vggface2').eval()
        self.transform = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def _get_results(self, image: Image, show=False):
        if image.mode != 'RGB':
            image = image.convert('RGB')
        results = self.yolo(image)
        if show:
            for result in results:
                result.show()
        return results

    def bounding_boxes(self, image: Image):
        results = self._get_results(image)
        boxes = results[0].boxes.xyxy.cpu().numpy().tolist()
        return boxes

    def crop_images(self, image: Image, boxes):
        cropped_images = []
        for (x1, y1, x2, y2) in boxes:
            cropped_image = image.crop((x1, y1, x2, y2))
            cropped_images.append(cropped_image)
        return cropped_images

    def vectorize_face(self, image: Image):
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0)
        with torch.no_grad():
            embedding = self.facenet(image_tensor)
        return embedding.numpy().tolist()

    def vectorize_faces(self, image: Image):
        faces = self.crop_images(image, self.bounding_boxes(image))
        vectors = [self.vectorize_face(face) for face in faces]
        # return np.array(vectors)
        return vectors