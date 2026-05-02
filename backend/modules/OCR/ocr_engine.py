# backend/modules/OCR/ocr_engine.py
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
import unicodedata

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # 1. IMAGE OPTIMIZATION (Essential for general accuracy)
        img = img.convert('L') 
        img = ImageEnhance.Contrast(img).enhance(2.3) # Slightly higher for better edge detection
        img = img.filter(ImageFilter.SHARPEN)
        
        # 2. LSTM EXTRACTION
        # --oem 1 uses the neural network which is better for Sinhala ligatures
        raw_text = pytesseract.image_to_string(img, lang='sin', config='--psm 3 --oem 1')
        
        if not raw_text:
            return ""

        # 3. GLOBAL UNICODE NORMALIZATION (The General Fix)
        # NFC standardizes the "broken" parts Tesseract creates into single characters
        text = unicodedata.normalize('NFC', raw_text)

        # 4. REGEX REPAIR (Fixes the Rakaaraansaya/Yansaya structure globally)
        # These patterns fix character segmentation errors across the entire Sinhala script
        
        # Fix Rakaaraansaya (e.g., ප්ර -> ප්‍ර)
        text = re.sub(r'([ක-ෆ])්ර', r'\1්‍ර', text)
        
        # Fix Yansaya (e.g., ත්ය -> ත්‍ය)
        text = re.sub(r'([ක-ෆ])්ය', r'\1්‍ය', text)
        
        # Fix Hal-Kiri (e.g., න්‍යා -> න්‍යා)
        text = re.sub(r'([ක-ෆ])්([යර])', r'\1්\2', text)

        # 5. CLEANUP
        text = text.replace('\n', ' ') # Remove newlines that break web queries
        clean_text = " ".join(text.split()) # Remove duplicate spaces

        return clean_text.strip()
        
    except Exception as e:
        print(f"❌ OCR Backend Error: {e}")
        return None