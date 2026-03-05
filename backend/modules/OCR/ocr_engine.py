# backend/modules/OCR/ocr_engine.py
import pytesseract
from PIL import Image
import io
import re


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from PIL import Image, ImageEnhance, ImageFilter

def extract_text_from_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # --- NEW: Image Pre-processing for better Sinhala Recognition ---
        img = img.convert('L') # Convert to Grayscale
        img = ImageEnhance.Contrast(img).enhance(2.0) # Boost contrast
        img = img.filter(ImageFilter.SHARPEN) # Sharpen edges
        
        # Use '--oem 1' for LSTM neural network recognition
        extracted_text = pytesseract.image_to_string(img, lang='sin', config='--psm 3 --oem 1')
        
        # Clean up newlines that break the search query
        clean_text = extracted_text.replace('\n', ' ').strip()
        return " ".join(clean_text.split())
        
    except Exception as e:
        print(f"❌ OCR Backend Error: {e}")
        return None