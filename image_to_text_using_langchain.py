import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import base64

def generate_scene_description(image_bytes):
    # Read API key from file
    with open("keys/gemini_key.txt", "r") as f:
        api_key = f.read().strip()

    # Initialize the LangChain model with the Gemini API
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=api_key)

    # Encode image to base64
    image_data = base64.b64encode(image_bytes).decode("utf-8")

    # Create a message with image and prompt
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Describe the scene in the uploaded image."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
        ],
    )

    # Invoke the model
    response = model.invoke([message])

    # Return response content
    return response.content

def main():
    st.title("Real-Time Scene Understanding")

    # File uploader
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image_bytes = uploaded_file.read()
        text_description = generate_scene_description(image_bytes)
        st.write(text_description)

if __name__ == "__main__":
    main()
