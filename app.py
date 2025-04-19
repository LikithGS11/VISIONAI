import streamlit as st
from PIL import Image
import os
from utils.scene_understanding import generate_scene_description
from utils.text_to_speech import text_to_speech
from utils.object_detection import detect_objects
from utils.personalized_assistance import provide_personalized_assistance
from utils.ocr_processing import extract_text_from_image
import io
import base64
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="AI-Powered Vision Assistant",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "# AI Vision Assistant\nHelping visually impaired individuals navigate their world."
    }
)

# Custom CSS for improved design
def load_css():
    css = """
    <style>
        /* Main layout and theme */
        .main {
            background-color: #121212;
            color: #f0f0f0;
        }
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styling */
        .header {
            padding: 1.5rem;
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .app-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #ff7e5f, #feb47b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .app-description {
            font-size: 1.1rem;
            opacity: 0.8;
            margin-bottom: 0;
        }
        
        /* Features display */
        .features-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 1.5rem;
            flex: 1 1 200px;
            min-width: 200px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-align: center;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .feature-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #ffffff;
        }
        
        .feature-description {
            font-size: 0.9rem;
            color: #b0b0b0;
        }
        
        /* Upload section */
        .upload-section {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .upload-header {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #ffffff;
        }
        
        .upload-area {
            border: 2px dashed #4e5d78;
            border-radius: 10px;
            padding: 3rem 1rem;
            text-align: center;
            cursor: pointer;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            border-color: #feb47b;
            background-color: rgba(255, 126, 95, 0.05);
        }
        
        /* Analysis section */
        .analysis-section {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Button styling */
        .custom-button {
            background: linear-gradient(90deg, #ff7e5f 0%, #feb47b 100%);
            color: white;
            border: none;
            border-radius: 20px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            margin-bottom: 0.5rem;
        }
        
        .custom-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* Results styling */
        .result-container {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .result-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #feb47b;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            padding: 1rem;
            margin-top: 2rem;
            opacity: 0.7;
            font-size: 0.9rem;
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
            background-color: #2d2d2d;
            border-radius: 5px 5px 0px 0px;
            gap: 10px;
            padding-top: 10px;
            padding-bottom: 10px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #3d3d3d !important;
            border-bottom: 2px solid #feb47b !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-top-color: #feb47b !important;
        }
        
        /* Image display */
        .uploaded-image-container {
            padding: 1rem;
            background-color: #2d2d2d;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        
        /* Audio player */
        .stAudio > div {
            background-color: #2d2d2d;
            border-radius: 8px;
        }
        
        /* Notification styling */
        .success-notification {
            padding: 1rem;
            background-color: rgba(40, 167, 69, 0.2);
            border-left: 5px solid #28a745;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .warning-notification {
            padding: 1rem;
            background-color: rgba(255, 193, 7, 0.2);
            border-left: 5px solid #ffc107;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .error-notification {
            padding: 1rem;
            background-color: rgba(220, 53, 69, 0.2);
            border-left: 5px solid #dc3545;
            border-radius: 5px;
            margin: 1rem 0;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Load the custom CSS
load_css()

# Header section
st.markdown("""
<div class="header">
    <h1 class="app-title">AI-Powered Vision Assistant</h1>
    <p class="app-description">Enhancing everyday experiences for visually impaired individuals through artificial intelligence</p>
</div>
""", unsafe_allow_html=True)

# Features section
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

# Upload section
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.markdown('<h2 class="upload-header">Upload an Image</h2>', unsafe_allow_html=True)
st.markdown('<p>Please upload an image (Max 5MB) to explore the features above!</p>', unsafe_allow_html=True)

# Create columns for upload area and demo button
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_image = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

with col2:
    if st.button("Try Demo Image", key="demo_btn", help="Use a sample image to test the features"):
        # Path to demo image
        demo_image_path = Path("demo/sample_image.jpg")
        
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
            
            # Create images directory if it doesn't exist
            os.makedirs("images", exist_ok=True)
            
            # Create audio directory if it doesn't exist
            os.makedirs("audio", exist_ok=True)
            
            # Save the image to the "images" folder
            save_path = os.path.join("images", uploaded_image.name)
            image.save(save_path)
            
            # Store the image in session state
            st.session_state.image = image
            st.session_state.image_path = save_path
            st.session_state.using_demo = False
            
            # Success message
            st.markdown("""
            <div class="success-notification">
                <strong>Success!</strong> Image uploaded successfully. Select a feature below to analyze.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-notification">
                <strong>Error!</strong> The file size exceeds the 5MB limit. Please upload a smaller image.
            </div>
            """, unsafe_allow_html=True)
    
    # Use the image from session state (either uploaded or demo)
    if 'image' in st.session_state:
        image = st.session_state.image
        
        # Display the image
        st.markdown('<div class="uploaded-image-container">', unsafe_allow_html=True)
        st.image(image, caption="Image Ready for Analysis", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Feature selection with tabs
        st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
        st.markdown('<h2>Select Analysis Feature</h2>', unsafe_allow_html=True)
        
        tabs = st.tabs(["Scene Understanding", "Text-to-Speech", "Object Detection", "Personalized Assistance"])
        
        with tabs[0]:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
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
                                # Create audio directory if it doesn't exist
                                os.makedirs("audio", exist_ok=True)
                                
                                # Path for saving audio
                                output_audio_path = "audio/scene_description.mp3"
                                
                                # Convert description to speech
                                text_to_speech(description, output_audio_path)
                                
                                # Provide audio playback
                                st.audio(output_audio_path, format="audio/mp3")
                                
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            
        with tabs[1]:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
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
                                        file_name="extracted_text_audio.mp3",
                                        mime="audio/mp3"
                                    )
                            else:
                                st.markdown("""
                                <div class="warning-notification">
                                    <strong>Note:</strong> No text detected in the uploaded image.
                                </div>
                                """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")

        with tabs[2]:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Detect Objects & Obstacles", key="obj_btn", help="Identify objects and potential obstacles"):
                    with st.spinner("Detecting objects..."):
                        try:
                            st.markdown('<div class="result-container">', unsafe_allow_html=True)
                            st.markdown('<h3 class="result-title">Detected Objects</h3>', unsafe_allow_html=True)
                            
                            # Detect objects
                            detected_image = detect_objects(image)
                            st.image(detected_image, caption="Objects & Obstacles Detected", use_column_width=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")

        with tabs[3]:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
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
                                # Create audio directory if it doesn't exist
                                os.makedirs("audio", exist_ok=True)
                                
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
        
        # Reset button to clear the current image
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
                st.rerun()

# Help section with collapsible content
with st.sidebar:
    st.title("Help & Information")
    
    with st.expander("How to Use This App"):
        st.write("""
        1. Upload an image by clicking the upload area or use the demo image
        2. Select one of the analysis features from the tabs
        3. View the results and use additional options like listening to audio
        """)
    
    with st.expander("About the Features"):
        st.write("""
        - **Scene Understanding**: Provides detailed descriptions of the surroundings in the image
        - **Text-to-Speech**: Extracts text from images and converts it to spoken audio
        - **Object Detection**: Identifies objects and potential obstacles in the image
        - **Personalized Assistance**: Offers context-specific guidance based on the scene
        """)
    
    with st.expander("Accessibility Tips"):
        st.write("""
        - Use keyboard shortcuts for navigation (Tab to move, Enter to select)
        - All audio can be downloaded for offline listening
        - Results can be expanded or collapsed as needed
        - The app works with screen readers
        """)

    with st.expander("About the Team"):
        st.write("""
        - **LIKITH G S**
        - **DAYANA G S**
        - **MANISHA KOLI**
        - **ANANYA V**         
        """)    
    
    st.divider()
    st.caption("© 2025 AI-Powered Vision Assistant")
    st.caption("Enhancing accessibility through technology")

# Footer
st.markdown("""
<div class="footer">
    <p>AI-Powered Vision Assistant | Enhancing accessibility through technology</p>
</div>
""", unsafe_allow_html=True)

# Add keyboard shortcuts
st.markdown("""
<script>
    document.addEventListener('keydown', function(e) {
        // Add keyboard shortcuts here if needed
    });
</script>
""", unsafe_allow_html=True)