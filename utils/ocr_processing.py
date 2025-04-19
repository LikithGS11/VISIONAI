from PIL import Image
import pytesseract

# ✅ Set the correct path to tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Likith G S\Desktop\JUPYTER NOTEBOOK\tesseract.exe"

# Function to extract text from an image using Tesseract OCR
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text
