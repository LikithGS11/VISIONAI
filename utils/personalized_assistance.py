import os
import google.generativeai as genai

# Analyze the uploaded image and provide personalized guidance or assistance.
def provide_personalized_assistance(image):
    try:
        # Read the Gemini API key from the environment (see .env / .env.example)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return (
                "GOOGLE_API_KEY is not set. Add it to your .env file (see .env.example)."
            )

        # Configure the Google API with the provided API key
        genai.configure(api_key=api_key)

        # Initialize a Generative AI model with the provided model name and API key
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # Create a task-specific prompt that instructs the model to analyze the image
        # and provide personalized suggestions (e.g., identifying objects, context, etc.)
        prompt = (
            "Analyze the uploaded image and provide personalized suggestions. "
            "Describe objects, labels, or context that can assist the user in daily tasks."
        )

        # Generate response using the Generative AI API
        # The response will be the generated text based on the image and prompt.
        response = model.generate_content([image, prompt])

        # Check if the response exists, and return the content if available
        if response:
            return response.text
        else:
            return "Unable to provide personalized guidance."

    except Exception as e:
        # If an error occurs, capture the exception and return a message with the error details
        return f"Error occurred while processing the image: {e}"
