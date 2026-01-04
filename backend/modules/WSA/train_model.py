import pandas as pd
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from preprocessor import SinhalaPreprocessor

def train():
    print("🚀 වාර්තා 1000+ ක දත්ත සමුදාය සමඟ පුහුණු කිරීම ආරම්භ වේ...")
    
    # වර්තමාන ෆෝල්ඩරයේ ඇති CSV ගොනුව සොයා ගැනීම
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'training_data.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ දෝෂයකි: {csv_path} ගොනුව හමු නොවීය!")
        return

    df = pd.read_csv(csv_path)
    pre = SinhalaPreprocessor()
    processed_texts = []
    
    print("🧹 දත්ත පිරිසිදු කිරීම සහ විශේෂාංග වෙන් කර ගැනීම සිදු වේ...")
    
    for index, row in df.iterrows():
        # එක් එක් පේළිය පිරිසිදු කිරීම
        clean_text = pre.preprocess_sinhala(row['text'])
        if clean_text:
            processed_texts.append(clean_text)

    # 1. Vectorizer එක සකස් කිරීම
    vectorizer = TfidfVectorizer()
    
    # 2. දත්ත පුහුණු කිරීම (Fitting the model)
    tfidf_matrix = vectorizer.fit_transform(processed_texts)
    
    # 3. නව .pkl ගොනු ලෙස ගබඩා කිරීම
    joblib.dump(vectorizer, os.path.join(current_dir, 'vectorizer.pkl'))
    joblib.dump(tfidf_matrix, os.path.join(current_dir, 'tfidf_matrix.pkl'))
    
    print(f"==================================================")
    print(f"🎉 සාර්ථකයි: වාර්තා {len(processed_texts)} ක් ඇසුරෙන් පද්ධතිය පුහුණු කළා.")
    print(f"💾 vectorizer.pkl සහ tfidf_matrix.pkl යාවත්කාලීන විය.")
    print(f"==================================================")

if __name__ == "__main__":
    train()