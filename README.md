
---
# **VisionAI: AI-Powered Solution for Assisting Visually Impaired Individuals**

VisionAI is an innovative solution designed to empower visually impaired individuals by providing advanced real-time scene understanding, text-to-speech conversion, object detection, and personalized assistance. By leveraging cutting-edge AI technologies, VisionAI aims to create an intuitive and life-enhancing tool that enhances the user's ability to interact with and navigate their surroundings.

---

## Tools and Libraries Used in VisionAI

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Ultralytics](https://img.shields.io/badge/Ultralytics-41b883?style=flat&logo=ultralytics&logoColor=white)](https://ultralytics.com)
[![Pillow](https://img.shields.io/badge/Pillow-3C1A74?style=flat&logo=pillow&logoColor=white)](https://python-pillow.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org/)
[![Numpy](https://img.shields.io/badge/Numpy-013243?style=flat&logo=numpy&logoColor=white)](https://numpy.org/)
[![PyTesseract](https://img.shields.io/badge/PyTesseract-FF4500?style=flat)](https://github.com/madmaze/pytesseract)
[![Google Generative AI](https://img.shields.io/badge/Google%20Generative%20AI-4285F4?style=flat&logo=google&logoColor=white)](https://developers.google.com/ai)
[![LangChain](https://img.shields.io/badge/LangChain-0E76A8?style=flat)](https://langchain.com/)
[![LangChain Core Messages](https://img.shields.io/badge/LangChain%20Core%20Messages-0E76A8?style=flat)](https://langchain.com/)
[![PyTTSX3](https://img.shields.io/badge/PyTTSX3-9ACD32?style=flat)](https://pypi.org/project/pyttsx3/)

---

## **Key Features**

- **Real-Time Scene Understanding**: Utilizes AI to analyze images and generate descriptive text, providing visually impaired users with an understanding of the content around them.
  
- **Text-to-Speech Conversion**: Employs OCR technology to extract text from images and converts it into audible speech for easy consumption.
  
- **Object and Obstacle Detection**: Identifies and highlights objects or obstacles in the environment to aid users in avoiding hazards and recognizing important objects.
  
- **Personalized Assistance**: Offers tailored guidance for a variety of daily tasks, such as reading labels, recognizing items, and understanding the environment.

---

## **Project Workflow**

### 1. **Problem Identification**
   - **Challenge**: Visually impaired individuals encounter significant obstacles in navigating their environment, reading printed content, and performing everyday tasks that require sight.
   - **Solution**: VisionAI was created to help visually impaired individuals by providing a user-friendly interface with real-time feedback and intuitive functionalities.

### 2. **Planning and Design**
   - **Design Goals**:  
     - Create an easy-to-use web application with capabilities such as image uploads, real-time analysis, and text-to-speech output.
     - Incorporate AI-driven object detection and obstacle recognition to improve situational awareness.

### 3. **Development and Implementation**
   - **Core Technologies**:  
     - **LangChain**: Used to integrate natural language processing and AI-driven functionalities.
     - **Streamlit**: For building an interactive and responsive web application.
     - **Google Generative AI**: To enhance scene understanding and object detection through advanced machine learning.
     - **OpenCV and PyTesseract**: For computer vision tasks like OCR and image processing.
   
   - **Developed Features**:  
     - Real-time scene understanding through computer vision techniques.
     - OCR-based text extraction with text-to-speech conversion for enhanced accessibility.
     - Object and obstacle detection, providing users with visual cues and contextual information.

### 4. **Testing**
   - The application underwent extensive testing to ensure high accuracy in object detection, scene interpretation, and speech synthesis, ensuring it meets the needs of visually impaired users.

### 5. **Final Output**
   - **VisionAI** allows users to upload images, which are then processed for:  
     - **Scene Understanding**: The app provides a detailed description of the image contents.  
     - **Text-to-Speech Conversion**: Extracts any text in the image and reads it aloud.  
     - **Object and Obstacle Detection**: Identifies objects in the image, enhancing the user's awareness.  
     - **Personalized Assistance**: Offers help in daily tasks like reading labels or recognizing objects.

---

## **Requirements**

To run VisionAI locally, ensure the following dependencies are installed:

- Python 3.8 or higher  
- **LangChain**: `pip install langchain`  
- **Streamlit**: `pip install streamlit`  
- **Google Generative AI SDK**  
- **OpenCV**: `pip install opencv-python`  
- **PyTesseract**: `pip install pytesseract`
  
---
