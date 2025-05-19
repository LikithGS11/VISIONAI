import streamlit as st
from PIL import Image
import os
from utils.scene_understanding import generate_scene_description
from utils.text_to_speech import text_to_speech
from utils.object_detection import YOLODetector
from utils.personalized_assistance import provide_personalized_assistance
from utils.ocr_processing import extract_text_from_image
from utils.realtime_detection import real_time_object_detection_and_feedback
from utils.navigation_assistance import navigation_page
import io
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="VisionAI Assistant",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "# VISIONAI Assistant\nHelping visually impaired individuals navigate their world."
    }
)

# Custom CSS for improved design with new color scheme
def load_css():
    css = """
    <style>
        /* Main layout and theme */
        .main {
            background-color: #0a1929;
            color: #e6f1ff;
        }
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styling */
        .header {
            padding: 1.5rem;
            background: linear-gradient(90deg, #1a365d 0%, #2c5282 100%);
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }
        
        .app-title {
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #63b3ed, #4299e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .app-description {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 0;
            color: #a0aec0;
        }
        
        /* Features display */
        .features-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1.2rem;
            margin-bottom: 2rem;
        }
        
        .feature-card {
            background-color: #1e2a3a;
            border-radius: 12px;
            padding: 1.7rem;
            flex: 1 1 200px;
            min-width: 200px;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-align: center;
            border-left: 4px solid #4299e1;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.25);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .feature-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #63b3ed;
        }
        
        .feature-description {
            font-size: 0.95rem;
            color: #a0aec0;
        }
        
        /* Upload section */
        .upload-section {
            background-color: #1e2a3a;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            border-left: 4px solid #4299e1;
        }
        
        .upload-header {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #63b3ed;
        }
        
        .upload-area {
            border: 2px dashed #4299e1;
            border-radius: 10px;
            padding: 3rem 1rem;
            text-align: center;
            cursor: pointer;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            border-color: #63b3ed;
            background-color: rgba(66, 153, 225, 0.05);
        }
        
        /* Analysis section */
        .analysis-section {
            background-color: #1e2a3a;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
            border-left: 4px solid #4299e1;
        }
        
        /* Button styling */
        .custom-button {
            background: linear-gradient(90deg, #4299e1 0%, #63b3ed 100%);
            color: white;
            border: none;
            border-radius: 24px;
            padding: 0.7rem 1.7rem;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 0.7rem;
        }
        
        .custom-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* Results styling */
        .result-container {
            background-color: #2a4365;
            border-radius: 10px;
            padding: 1.7rem;
            margin-top: 1.5rem;
            border-left: 4px solid #63b3ed;
        }
        
        .result-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #63b3ed;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            padding: 1.5rem;
            margin-top: 2.5rem;
            opacity: 0.8;
            font-size: 0.9rem;
            background-color: #1a365d;
            border-radius: 8px;
            color: #a0aec0;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .features-container {
                flex-direction: column;
            }
            
            .feature-card {
                width: 100%;
            }
            
            .app-title {
                font-size: 2rem;
            }
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #2a4365;
            border-radius: 8px 8px 0px 0px;
            gap: 10px;
            padding-top: 10px;
            padding-bottom: 10px;
            color: #a0aec0;
        }

        .stTabs [aria-selected="true"] {
            background-color: #2c5282 !important;
            border-bottom: 3px solid #63b3ed !important;
            color: #e6f1ff !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-top-color: #63b3ed !important;
        }
        
        /* Image display */
        .uploaded-image-container {
            padding: 1.3rem;
            background-color: #2a4365;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Audio player */
        .stAudio > div {
            background-color: #2a4365;
            border-radius: 10px;
        }
        
        /* Notification styling */
        .success-notification {
            padding: 1.2rem;
            background-color: rgba(56, 161, 105, 0.2);
            border-left: 5px solid #38a169;
            border-radius: 6px;
            margin: 1.2rem 0;
            color: #c6f6d5;
        }
        
        .warning-notification {
            padding: 1.2rem;
            background-color: rgba(236, 201, 75, 0.2);
            border-left: 5px solid #ecc94b;
            border-radius: 6px;
            margin: 1.2rem 0;
            color: #fefcbf;
        }
        
        .error-notification {
            padding: 1.2rem;
            background-color: rgba(245, 101, 101, 0.2);
            border-left: 5px solid #f56565;
            border-radius: 6px;
            margin: 1.2rem 0;
            color: #fed7d7;
        }
        
        /* Improved sidebar styling */
        .css-1d391kg, .css-1cypcdb, .css-1868j9k {
            background-color: #1a365d;
        }
        
        .css-pkbazv {
            color: #63b3ed;
            font-size: 1.3rem;
            margin-bottom: 1rem;
        }
        
        .sidebar .sidebar-content {
            background-color: #1a365d;
        }
        
        .css-hxt7ib {  /* Navigation container */
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Radio buttons in sidebar */
        .st-cb, .st-bq, .st-az, .st-ae, .st-af, .st-ag, .st-ah, .st-ai, .st-aj {
            background-color: #2c5282;
            color: #e6f1ff;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #2a4365;
            border-radius: 8px;
            color: #63b3ed;
            padding: 0.8rem;
            font-weight: 600;
        }
        
        .streamlit-expanderContent {
            background-color: #1e2a3a;
            border-radius: 0 0 8px 8px;
            padding: 1rem;
            color: #a0aec0;
        }
        
        /* Divider in sidebar */
        hr {
            border-color: #4299e1;
            margin: 1.5rem 0;
        }
        
        /* Caption in sidebar */
        .css-1ydqiqk {
            color: #a0aec0;
            font-size: 0.85rem;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Load the custom CSS
load_css()

# Create directories if they don't exist
os.makedirs("images", exist_ok=True)
os.makedirs("audio", exist_ok=True)

# Initialize session states
if 'detection_running' not in st.session_state:
    st.session_state.detection_running = False

# Instantiate YOLODetector
detector = YOLODetector()

# --- Sidebar Navigation ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/yourusername/visionai-app/main/logo.png", width=100)
    st.title("VisionAI")
    
    # Navigation
    page = st.radio("Navigation", ["Home", "Image Analysis", "Real-Time Camera", "Navigation Assistance"])
    
    st.divider()
    
    # Help section
    st.subheader("Help & Information")
    
    with st.expander("How to Use This App"):
        st.write("""
        1. **Upload an image** on the Image Analysis page
        2. **Select a feature** from the tabs to analyze your image
        3. **View the results** and listen to audio descriptions
        4. Or use the **Real-Time Camera** for live object detection
        """)
    
    with st.expander("Features Guide"):
        st.write("""
        - **Scene Understanding**: Detailed scene descriptions
        - **Text-to-Speech**: Convert text in images to audio
        - **Object Detection**: Identify objects & obstacles
        - **Personalized Assistance**: Context-specific guidance
        - **Real-Time Camera**: Live object detection with voice feedback
        - **Navigation Assistance**: Help navigating through various locations
        """)
    
    with st.expander("Accessibility Tips"):
        st.write("""
        - Use **Tab** + **Enter** for keyboard navigation
        - All audio can be **downloaded** for offline listening
        - Results can be **expanded/collapsed** as needed
        - Compatible with **screen readers**
        """)

    with st.expander("About the Team"):
        st.write("""
        This application was developed by:
        
        - **LIKITH G S**
        - **DAYANA G S**
        - **MANISHA KOLI**
        - **ANANYA V**
        """)
    
    st.divider()
    st.caption("© 2025 VisionAI Assistant")
    st.caption("Enhancing accessibility through technology")

# --- Main Application Logic ---
if page == "Home":
    # Header section
    st.markdown("""
    <div class="header">
        <h1 class="app-title">VisionAI Assistant</h1>
        <p class="app-description">Enhancing everyday experiences for visually impaired individuals through artificial intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation buttons on home page
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    with nav_col1:
        if st.button("Home", key="nav_home"):
            st.experimental_set_query_params(page="Home")
    with nav_col2:
        if st.button("Image Analysis", key="nav_image_analysis"):
            st.experimental_set_query_params(page="Image Analysis")
    with nav_col3:
        if st.button("Real-Time Camera", key="nav_real_time_camera"):
            st.experimental_set_query_params(page="Real-Time Camera")
    with nav_col4:
        if st.button("Navigation Assistance", key="nav_navigation_assistance"):
            st.experimental_set_query_params(page="Navigation Assistance")

    # Welcome Message
    st.markdown("""
    ## Welcome to VisionAI
    
    VisionAI is an advanced assistive technology designed to help visually impaired individuals navigate and understand their surroundings with greater confidence and independence.
    
    ### Our Mission
    
    To leverage cutting-edge AI technologies to bridge the visual gap and provide real-time information about the surrounding environment, text recognition, and personalized guidance.
    
    ### How It Works
    
    Select "Image Analysis" from the sidebar to upload an image and analyze it, or choose "Real-Time Camera" for live object detection with voice feedback.
    """)
    
    # Features overview
    st.markdown("""
    <div class="features-container">
        <div class="feature-card">
            <div class="feature-icon">👁️</div>
            <div class="feature-title">Scene Understanding</div>
            <div class="feature-description">Detailed descriptions of surroundings to provide spatial awareness</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔊</div>
            <div class="feature-title">Text to Speech</div>
            <div class="feature-description">Converts written text from images into clear spoken words</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🚧</div>
            <div class="feature-title">Object Detection</div>
            <div class="feature-description">Identifies objects and potential obstacles in the path</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🤝</div>
            <div class="feature-title">Personalized Assistance</div>
            <div class="feature-description">Tailored guidance based on the specific environment</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("""
    <div class="analysis-section">
    <h2 style="color: #63b3ed;">Getting Started</h2>
    <p>To begin using VisionAI, navigate to the "Image Analysis" section from the sidebar menu to upload an image for processing, or try the "Real-Time Camera" feature for live detection.</p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Navigation Assistance":
    navigation_page()    

elif page == "Image Analysis":
    # Header section
    st.markdown("""
    <div class="header">
        <h1 class="app-title">Image Analysis</h1>
        <p class="app-description">Upload an image to analyze and receive detailed information through various AI features</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="upload-header">Upload an Image</h2>', unsafe_allow_html=True)
    st.markdown('<p>Please upload an image (Max 5MB) to explore our features!</p>', unsafe_allow_html=True)

    # Create columns for upload area and demo button
    col1, col2 = st.columns([3, 1])

    with col1:
        uploaded_image = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    with col2:
        if st.button("Try Demo Image", key="demo_btn", help="Use a sample image to test the features"):
            # Path to demo image
            demo_image_path = Path(r"images/ATSFHIGLVLE.jpg")
            
            # Check if demo image exists
            if demo_image_path.exists():
                # Open the demo image
                image = Image.open(demo_image_path)
                
                # Set the demo image as the current image in session state
                if 'image' not in st.session_state:
                    st.session_state.image = image
                    st.session_state.image_path = str(demo_image_path)
                    st.session_state.using_demo = True
                    st.rerun()
            else:
                st.error("Demo image not found. Please upload your own image.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Check if image is uploaded or demo is used
    if uploaded_image is not None or ('image' in st.session_state and st.session_state.get('using_demo', False)):
        
        # Process uploaded image if available
        if uploaded_image is not None:
            # Check if file size is within 5MB
            if uploaded_image.size <= 5 * 1024 * 1024:
                # Open the image
                image = Image.open(uploaded_image)
                
                # Save the image to the "images" folder
                save_path = os.path.join("images", uploaded_image.name)
                image.save(save_path)
                
                # Store the image in session state
                st.session_state.image = image
                st.session_state.image_path = save_path
                st.session_state.using_demo = False
                
                # Success message
                st.markdown('''
                <div class="success-notification">
                    <strong>Success!</strong> Image uploaded successfully. Select a feature below to analyze.
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown('''
                <div class="error-notification">
                    <strong>Error!</strong> The file size exceeds the 5MB limit. Please upload a smaller image.
                </div>
                ''', unsafe_allow_html=True)
        
        # Use the image from session state (either uploaded or demo)
        if 'image' in st.session_state:
            image = st.session_state.image
            
            # Display the image
            st.markdown('<div class="uploaded-image-container">', unsafe_allow_html=True)
            st.image(image, caption="Image Ready for Analysis", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Feature selection with tabs
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            st.markdown('<h2 style="color: #63b3ed;">Select Analysis Feature</h2>', unsafe_allow_html=True)
            
            tabs = st.tabs(["Scene Understanding", "Text-to-Speech", "Object Detection", "Personalized Assistance"])
            
            # Scene Understanding Tab
            with tabs[0]:
                st.subheader("Scene Understanding")
                st.write("Generate a detailed description of what's in the image to understand the surroundings.")
                
                if st.button("Generate Scene Description", key="scene_btn", help="Get a detailed description of the scene"):
                    with st.spinner("Analyzing scene..."):
                        try:
                            # Read the image file as bytes
                            img_byte_arr = io.BytesIO() 
                            image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
                            image_bytes = img_byte_arr.getvalue()

                            # Generate scene description
                            description = generate_scene_description(image_bytes)
                            
                            st.markdown('<div class="result-container">', unsafe_allow_html=True)
                            st.markdown('<h3 class="result-title">Scene Description</h3>', unsafe_allow_html=True)
                            st.write(description)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Add text-to-speech option for the description
                            if st.button("Listen to Description", key="listen_scene"):
                                # Path for saving audio
                                output_audio_path = "audio/scene_description.wav"
                                
                                # Convert description to speech
                                text_to_speech(description, output_audio_path)
                                
                                # Store audio path in session state for playback
                                st.session_state.scene_audio = output_audio_path
                            
                            # Play audio if available in session state
                            if 'scene_audio' in st.session_state:
                                st.audio(st.session_state.scene_audio, format="audio/wav")
                                
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            
            # Text-to-Speech Tab
            with tabs[1]:
                st.subheader("Text-to-Speech")
                st.write("Extract text from images and convert it to speech for easy listening.")
                
                if st.button("Extract & Convert Text", key="tts_btn", help="Extract text from image and convert to speech"):
                    with st.spinner("Processing text..."):
                        try:
                            text = extract_text_from_image(image)
                            if text.strip():
                                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                                st.markdown('<h3 class="result-title">Extracted Text</h3>', unsafe_allow_html=True)
                                st.write(text)
                                st.markdown('</div>', unsafe_allow_html=True)

                                # Path for saving audio
                                output_audio_path = "audio/output_audio.mp3"

                                # Convert extracted text to speech
                                text_to_speech(text, output_audio_path)

                                # Provide the audio for playback
                                st.markdown("""
                                <div class="success-notification">
                                    <strong>Success!</strong> Text has been successfully converted to speech.
                                </div>
                                """, unsafe_allow_html=True)
                                st.audio(output_audio_path, format="audio/mp3")
                                
                                # Download button
                                with open(output_audio_path, "rb") as file:
                                    btn = st.download_button(
                                        label="Download Audio File",
                                        data=file,
                                        file_name="output_audio.mp3",
                                        mime="audio/mp3"
                                    )
                            else:
                                st.warning("No text was detected in the image. Please try another image with visible text.")
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            
            # Object Detection Tab
            with tabs[2]:
                st.subheader("Object Detection")
                st.write("Identify objects and potential obstacles in the image.")
                
                if st.button("Detect Objects", key="detect_btn", help="Identify objects in the image"):
                    with st.spinner("Detecting objects..."):
                        try:
                            # Detect objects in the image and get annotated image and objects list
                            detected_image, objects = detector.detect(image)
                            
                            st.markdown('<div class="result-container">', unsafe_allow_html=True)
                            st.markdown('<h3 class="result-title">Detected Objects</h3>', unsafe_allow_html=True)
                            
                            # Display the annotated image
                            st.image(detected_image, caption="Objects Detected", use_container_width=True)
                            
                            if objects:
                                # Display detected objects details
                                for i, obj in enumerate(objects, 1):
                                    st.write(f"{i}. {obj['name']} - Confidence: {obj['confidence']:.2f}%")
                                    st.write(f"   Location: {obj['bbox']['x1']}, {obj['bbox']['y1']}, {obj['bbox']['x2']}, {obj['bbox']['y2']}")
                                
                                # Create a description of objects for text-to-speech
                                objects_description = "I detected the following objects: "
                                objects_description += ", ".join([obj['name'] for obj in objects])
                                objects_description += ". "
                                
                                for obj in objects:
                                    objects_description += f"There is a {obj['name']} located at coordinates {obj['bbox']['x1']}, {obj['bbox']['y1']}. "
                                
                                # Add text-to-speech option for object description
                                if st.button("Listen to Object Description", key="listen_objects"):
                                    # Path for saving audio
                                    output_audio_path = "audio/objects_description.mp3"
                                    
                                    # Convert objects description to speech
                                    text_to_speech(objects_description, output_audio_path)
                                    
                                    # Provide audio playback
                                    st.audio(output_audio_path, format="audio/mp3")
                            else:
                                st.write("No objects were detected in the image.")
                                
                            st.markdown('</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            
            # Personalized Assistance Tab
            with tabs[3]:
                st.subheader("Personalized Assistance")
                st.write("Receive context-specific guidance based on what's in the image.")
                
                if st.button("Get Personalized Guidance", key="assist_btn", help="Receive context-specific assistance"):
                    with st.spinner("Generating personalized assistance..."):
                        try:
                            st.markdown('<div class="result-container">', unsafe_allow_html=True)
                            st.markdown('<h3 class="result-title">Task-Specific Guidance</h3>', unsafe_allow_html=True)
                            
                            # Generate personalized assistance
                            guidance = provide_personalized_assistance(image)
                            st.write(guidance)
                            
                            # Add text-to-speech option for the guidance
                            if st.button("Listen to Guidance", key="listen_guidance"):
                                # Path for saving audio
                                output_audio_path = "audio/guidance_audio.mp3"
                                
                                # Convert guidance to speech
                                text_to_speech(guidance, output_audio_path)
                                
                                # Provide audio playback
                                st.audio(output_audio_path, format="audio/mp3")
                                
                            st.markdown('</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")

            st.markdown('</div>', unsafe_allow_html=True)
            
            # Reset Button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Reset & Upload New Image", key="reset_btn"):
                    # Clear the session state
                    if 'image' in st.session_state:
                        del st.session_state.image
                    if 'image_path' in st.session_state:
                        del st.session_state.image_path
                    if 'using_demo' in st.session_state:
                        del st.session_state.using_demo
                    if 'scene_audio' in st.session_state:
                        del st.session_state.scene_audio
                    st.rerun()

elif page == "Real-Time Camera":
    # Header section
    st.markdown("""
    <div class="header">
        <h1 class="app-title">Real-Time Camera</h1>
        <p class="app-description">Live object detection with voice feedback for real-time assistance</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="analysis-section">
    <h2 style="color: #63b3ed;">Real-Time Object Detection</h2>
    <p>This feature uses your device's camera to detect objects in real-time and provides voice feedback about what it sees. It's particularly useful for navigating unfamiliar environments or identifying objects around you.</p>
    
    <p><strong>How it works:</strong></p>
    <ol>
        <li>Click the "Start Camera Detection" button below</li>
        <li>Allow camera access when prompted</li>
        <li>The system will analyze the video feed and speak out detected objects</li>
        <li>Click "Stop Camera Detection" when you&apos;re done</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Camera access section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="upload-header">Camera Access</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.detection_running:
            if st.button("Start Camera Detection", key="camera_start", help="Begin real-time object detection"):
                st.session_state.detection_running = True
                st.markdown("""
                <div class="success-notification">
                    <strong>Starting camera...</strong> Please allow camera access when prompted.
                </div>
                """, unsafe_allow_html=True)
                real_time_object_detection_and_feedback()
        else:
            if st.button("Stop Camera Detection", key="camera_stop", help="Stop real-time object detection"):
                st.session_state.detection_running = False
                st.markdown("""
                <div class="warning-notification">
                    <strong>Camera stopped.</strong> Real-time detection has been stopped.
                </div>
                """, unsafe_allow_html=True)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Camera usage tips
    st.markdown("""
    <div class="analysis-section">
    <h3 style="color: #63b3ed;">Tips for Best Results</h3>
    <ul>
        <li>Ensure good lighting for better detection accuracy</li>
        <li>Keep the camera stable when possible</li>
        <li>Move the camera slowly to allow for better detection</li>
        <li>For text reading, hold the camera steady and close to the text</li>
        <li>The system works best with common objects and clear scenes</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Privacy notice
    st.markdown("""
    <div class="result-container">
    <h3 class="result-title">Privacy Notice</h3>
    <p>Your camera feed is processed locally on your device. No video is stored or transmitted to remote servers. The system only uses the feed for real-time object detection to provide immediate audio feedback.</p>
    </div>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div class="footer">
    <p>VisionAI Assistant | Enhancing accessibility through technology</p>
    <p>Version 2.0 | &copy; 2025</p>
</div>
""", unsafe_allow_html=True)

# Keyboard shortcuts script (removed for Streamlit compatibility)
# Streamlit does not support <script> tags in markdown for security reasons.