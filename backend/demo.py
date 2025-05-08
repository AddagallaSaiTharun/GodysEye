import cv2
import numpy as np
from PIL import Image
from app.utilities.yolo_facenet import Model
from sklearn.metrics.pairwise import cosine_similarity
from deepface import DeepFace

# Initialize model
detector = Model()

# Image paths
image_path_1 = r"backend\databases\video_db\cam-ce954929-d47e-4fc9-a416-bd3cf8ec2dad\frame_10.jpeg"
image_path_2 = r"backend\demo Dataset\WhatsApp Image 2025-05-06 at 2.35.35 PM (1).jpeg"



# Load images
image1 = Image.open(image_path_1).convert("RGB")
image2 = Image.open(image_path_2).convert("RGB")


# vec_1 = detector.vectorize_face(image1)
# vec_2 = detector.vectorize_face(image2)

# print(cosine_similarity(np.array(vec_1).reshape(1, -1), np.array(vec_2).reshape(1, -1)))
# image1.show()
# image2.show()
# # Get bounding boxes and embeddings
boxes1 = detector.bounding_boxes(image1)
crop_image1 = detector.crop_images(image1,boxes1)[0]
boxes2 = detector.bounding_boxes(image2)
crop_image2 = detector.crop_images(image2,boxes2)[0]

embeddings1 = DeepFace.represent(np.array(crop_image1), model_name="ArcFace")[0]["embedding"]
embeddings2 = DeepFace.represent(np.array(crop_image2), model_name="ArcFace")[0]["embedding"]

# Convert PIL image1 to OpenCV format for visualization
frame1 = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2BGR)

# Compare all faces in image 1 to the first face in image 2
if embeddings2:
    target_embedding = np.array(embeddings2[0]).reshape(1, -1)
    
    for i, (embedding, box) in enumerate(zip(embeddings1, boxes1)):
        similarity = cosine_similarity([embedding], target_embedding)[0][0]
        x1, y1, x2, y2 = map(int, box)

        # Draw bounding box
        cv2.rectangle(frame1, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Put similarity score
        label = f"Sim: {similarity:.2f}"
        cv2.putText(frame1, label, (x1-50, y1+50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Display result
    cv2.imshow("Similarity to Image 2", frame1)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("No faces detected in Image 2 to compare.")


