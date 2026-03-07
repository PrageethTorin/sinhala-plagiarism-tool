import pandas as pd
import re

CSV_FILE = 'training_data.csv'

def polish_data():
    print(f"🧹 Cleaning {CSV_FILE} for research excellence...")
    df = pd.read_csv(CSV_FILE)
    
    # 1. Remove rows with English letters
    df = df[~df['text'].str.contains(r'[a-zA-Z]', na=False)]
    
    # 2. Drop duplicates to ensure a diverse baseline
    df.drop_duplicates(subset=['text'], inplace=True)
    
    # 3. Final character cleaning
    df['text'] = df['text'].apply(lambda x: re.sub(r'[^\w\s\u0D80-\u0DFF]', '', str(x)))
    
    df.to_csv(CSV_FILE, index=False)
    print(f"✨ Success: Final Dataset Size is now {len(df)} Sinhala records.")

if __name__ == "__main__":
    polish_data()