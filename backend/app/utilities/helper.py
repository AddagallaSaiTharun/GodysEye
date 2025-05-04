from PIL import Image
import numpy as np
import cv2
from jose import jwt
from datetime import datetime, timedelta
from app.utilities.logger_config import logger
from app.utilities import config

def draw_box(image: np.ndarray, box: list, color=(255, 0, 0), thickness=6):
    if isinstance(image, Image.Image):
        image = np.array(image)
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    # cropped_image = image.crop((x1, y1, x2, y2))
    return image



def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)