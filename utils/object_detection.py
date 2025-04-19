from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image

# Detect objects using YOLOv5 models
def detect_objects(image):
 
    # Load Pre-trained YOLOv5 model
    model = YOLO("yolov5s.pt")  

    # Convert PIL image to OpenCV format
    opencv_image = np.array(image)
    opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)

    # Perform object detection
    results = model.predict(opencv_image)

    # Extract detection results
    detections = results[0].boxes.data  

    # Draw bounding boxes 
    for detection in detections:
        x1, y1, x2, y2, conf, cls = map(int, detection[:6])  # Convert to integers
        class_name = results[0].names[cls]

        # Draw bounding box
        cv2.rectangle(opencv_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw class label
        label = f"{class_name} {conf:.2f}"
        cv2.putText(
            opencv_image,
            label,
            (x1, y1 - 10),  # Position above bounding box
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,  # Font size
            (0, 0, 255),  # Red color
            2  # Thickness of text
        )

    # Convert back to PIL image for Streamlit
    detected_image = Image.fromarray(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB))
    return detected_image


############################## **simple methods** #####################################################

# from ultralytics import YOLO
# import numpy as np
# from PIL import Image

# def detect_objects(image):
#     """
#     Detect objects using YOLOv5 with the Ultralytics library.
#     """
#     # Load YOLOv5 model
#     model = YOLO("yolov5s.pt")  # Use a pre-trained YOLOv5 small model

#     # Convert PIL image to OpenCV format
#     opencv_image = np.array(image)
#     opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)

#     # Perform object detection
#     results = model.predict(opencv_image)

#     # Annotate detections on the image
#     annotated_image = results[0].plot()

#     # Convert back to PIL image for Streamlit
#     detected_image = Image.fromarray(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
#     return detected_image
