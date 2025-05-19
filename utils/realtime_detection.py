from ultralytics import YOLO
import cv2
import time
import threading
import numpy as np
import streamlit as st
from gtts import gTTS
from playsound import playsound
import uuid
import os

# Lock to prevent simultaneous audio playback
voice_lock = threading.Lock()

def speak(text):
    with voice_lock:
        try:
            filename = f"temp_{uuid.uuid4()}.mp3"
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
            playsound(filename)
            os.remove(filename)
        except Exception as e:
            st.error(f"Voice feedback failed: {e}")

def real_time_object_detection():
    model = YOLO("yolov8m.pt")
    cap = cv2.VideoCapture(0)

    last_spoken_time = 0
    cooldown = 5  # seconds
    last_labels_spoken = set()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        detected_labels = set()

        for box in results[0].boxes:
            cls = int(box.cls[0])
            label = results[0].names[cls]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detected_labels.add(label)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        current_time = time.time()
        if current_time - last_spoken_time > cooldown:
            new_labels = detected_labels - last_labels_spoken
            if new_labels:
                sentence = "I see " + ", ".join(new_labels)
                threading.Thread(target=speak, args=(sentence,), daemon=True).start()
                last_spoken_time = current_time
                last_labels_spoken.update(new_labels)

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        yield rgb_frame

    cap.release()
