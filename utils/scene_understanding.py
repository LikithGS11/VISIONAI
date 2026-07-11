# import google.generativeai as genai
# def generate_scene_description(image):
    
#     # Open and read API key
#     f = open("keys/gemini_key.txt")
#     key = f.read()

#     # configure genai key
#     genai.configure(api_key=key)

#     # Initialize a Generative AI model with the provided model name and API key
#     model = genai.GenerativeModel(model_name="gemini-1.5-flash")

#     # Create a simple prompt to describe the image
#     prompt = "Describe the scene in the uploaded image."

#     # Call the Generative AI API to generate the content
#     response = model.generate_content([image, prompt])

#     # Return the generated description or an error message
#     if response:
#        return response.text  
#     else:
#        return "Sorry, I couldn't describe the scene."


############################### **Using LangChain** #######################################

import os
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def generate_scene_description(image_bytes):
    # Read the Gemini API key from the environment (see .env / .env.example)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env file (see .env.example)."
        )

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
