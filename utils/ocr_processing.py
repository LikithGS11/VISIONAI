import os
from PIL import Image
import pytesseract

# Point pytesseract at the Tesseract executable.
# Configurable via the TESSERACT_PATH env var (see .env.example); defaults to
# "tesseract" which works when it is available on the system PATH.
_tesseract_cmd = os.getenv("TESSERACT_PATH", "tesseract")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

# Function to extract text from an image using Tesseract OCR
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text
