# **Tools and Libraries Used in Our Project**

<div style="display: flex; flex-wrap: wrap; gap: 10px;">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white" alt="Streamlit" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/Ultralytics-41b883?style=flat&logo=ultralytics&logoColor=white" alt="Ultralytics" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/Pillow-3C1A74?style=flat&logo=pillow&logoColor=white" alt="Pillow" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white" alt="OpenCV" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/Numpy-013243?style=flat&logo=numpy&logoColor=white" alt="Numpy" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/PyTesseract-FF4500?style=flat" alt="PyTesseract" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/Google%20Generative%20AI-4285F4?style=flat&logo=google&logoColor=white" alt="Google Generative AI" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/LangChain%20Google%20GenAI-0E76A8?style=flat" alt="LangChain Google GenAI" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/LangChain%20Core%20Messages-0E76A8?style=flat" alt="LangChain Core Messages" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/LangChain-0E76A8?style=flat" alt="LangChain" style="flex: 1 1 30%;">
  <img src="https://img.shields.io/badge/PyTTSX3-9ACD32?style=flat" alt="PyTTSX3" style="flex: 1 1 30%;">
</div> 

# AI-Powered Solution for Assisting Visually Impaired Individuals  

This project is designed to assist visually impaired individuals in understanding and interacting with their surroundings. Leveraging the power of Generative AI, it provides functionalities like real-time scene understanding, text-to-speech conversion, object detection, and personalized assistance for various tasks.  

## Features  

- **Real-Time Scene Understanding**: Generates descriptive text to interpret the uploaded image's content.  
- **Text-to-Speech Conversion**: Extracts text from the image using OCR techniques and converts it into audible speech.  
- **Object and Obstacle Detection**: Identifies objects and obstacles in the image and highlights them for improved situational awareness.  
- **Personalized Assistance**: Offers task-specific guidance, such as reading labels or recognizing items in the image.  

---

## Project Workflow  

### 1. **Problem Identification**  
   - Visually impaired individuals face challenges in navigating their environment, reading visual content, and performing tasks dependent on sight.  
   - The goal is to create a user-friendly AI application that addresses these challenges effectively.  

### 2. **Planning and Designing**  
   - Planned to build an application with:  
      - Image upload functionality.  
      - Real-time AI-powered features.  
      - Text-to-speech and obstacle detection capabilities.  

### 3. **Development and Implementation**  
   - **Technologies Used**:  
      - **LangChain**: For integrating language and AI capabilities.  
      - **Streamlit**: To create an interactive web application.  
      - **Google Generative AI APIs**: For advanced AI functionalities.  
   - **Features Developed**:  
      - Scene understanding using computer vision.  
      - OCR-based text-to-speech conversion.  
      - Object detection and labeling using AI models.  

### 4. **Testing**  
   - Verified the app's ability to accurately interpret images, extract text, and identify objects.  

### 5. **Final Output**  
   - The application accepts an image as input and performs:  
      - **Scene Analysis**: Displays descriptive text.  
      - **Text Extraction and Speech**: Reads text aloud.  
      - **Object Detection**: Highlights detected objects for better context.
      - **Personalized assistance**: Helps in daily tasks.

--- 

## Requirements  

To run this project locally, install the following:  

- Python 3.8 or higher  
- LangChain (`pip install langchain`)  
- Streamlit (`pip install streamlit`)  
- Google Generative AI SDK  
- OpenCV (`pip install opencv-python`)  
- PyTesseract (`pip install pytesseract`)  

---  

## Installation and Setup  

1. **Clone the Repository**  
   ```bash  
   git clone https://github.com/Angad143/Building-AI-Powered-Solution-for-Assisting-Visually-Impaired-Individuals.git
   cd AI-Visually-Impaired-Solution  
