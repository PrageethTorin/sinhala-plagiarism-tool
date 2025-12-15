from feature_extractor import SinhalaStylometryExtractor
from db_manager import DBManager

# 1. Sample Sinhala Text
sample_text = "මම අද ගෙදර ගියා. ඇය සහ මම පාඩම් කළා. මේක පරීක්ෂණයක්."
filename = "test_doc_001.txt"

# 2. Extract Features
extractor = SinhalaStylometryExtractor()
features = extractor.analyze_style(sample_text)
print("Extracted Features:", features)

# 3. Save to Database
db = DBManager()
try:
    doc_id = db.save_document(filename, sample_text)
    print(f"Document Saved with ID: {doc_id}")
    
    db.save_features(doc_id, features)
    print("Test Complete: Check your MySQL Database!")
except Exception as e:
    print("Error:", e)