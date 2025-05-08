from deepface import DeepFace

image_path_1 = r"C:\Users\tharu\OneDrive\Desktop\godseye\backend\demo Dataset\frame_110 2.jpeg"
image_path_2 = r"C:\Users\tharu\OneDrive\Desktop\godseye\backend\demo Dataset\WhatsApp Image 2025-05-06 at 2.35.35 PM (23).jpeg"
result = DeepFace.verify(img1_path = image_path_1, img2_path = image_path_2,model_name="Facenet512",enforce_detection=False)
print(result)