import requests

# Ensure your FastAPI backend (main.py) is running on this URL
URL = "http://127.0.0.1:8000/api/check-wsa"

def run_combined_test():
    # Test paragraph containing simple and complex Sinhala sentences
    test_paragraph = (
        "අද දින කාලගුණය ඉතාමත් සුන්දරය. අහස ඉතා පැහැදිලිව පවතී. කුරුල්ලෝ ගීත ගයති. " 
        "පාරිසරික සමතුලිතතාවය රැකගැනීම සඳහා ස්වභාවික සම්පත් කළමනාකරණය කිරීම සහ මිනිස් ක්‍රියාකාරකම් සීමා කිරීම අනාගත පරපුරේ පැවැත්ම උදෙසා අත්‍යවශ්‍යයෙන්ම කළ යුතු ඉතා වැදගත් වූත් කාලීන වූත් ක්‍රියාවලියකි. " 
        "මම මිදුලේ ඇවිද ගියෙමි. මල් පිපී තිබුණි. හිරු එළිය මැනවින් පවතී. "
    )

    try:
        # Send request to the FastAPI backend
        response = requests.post(URL, json={"text": test_paragraph})
        data = response.json()
        
        # Check if the expected key is in the response
        if 'style_change_ratio' in data:
            print("="*80)
            print("✅ DUAL-METRIC RESEARCH ANALYSIS (LENGTH & RICHNESS)")
            print(f"📊 Style Change Ratio: {data['style_change_ratio']}%")
            print("-" * 80)
            print(f"{'ID':<4} | {'Len':<5} | {'TTR %':<10} | {'Status'}")
            print("-" * 60)
            
            for s in data['sentence_map']:
                status = "🚩 STYLE SHIFT" if s['is_outlier'] else "✓ Baseline"
                print(f"S{s['id']:<3} | {s['length']:<5} | {s['lexical_ttr']:<10} | {status}")
            print("-" * 80)
        else:
            # Print the error from backend if keys are missing
            print("❌ Backend Error Response:", data)

    except Exception as e:
        print(f"❌ Connection Error: Could not reach backend at {URL}. Error: {e}")

if __name__ == "__main__":
    run_combined_test()