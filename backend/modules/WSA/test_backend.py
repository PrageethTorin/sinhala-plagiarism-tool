import requests
import json

# Configuration
URL = "http://127.0.0.1:8000/api/check-wsa"

def run_single_paragraph_test():
    print("="*75)
    print("WSA RESEARCH: SINGLE CONTINUOUS PARAGRAPH ANALYSIS")
    print("="*75)

    # Use triple quotes (""") to define a single multi-line paragraph string.
    # This simulates a user copying and pasting a 400+ word block into your system.
    test_paragraph = """අධ්‍යාපනය ඉතාම වැදගත්ය. මම පාසල් යන්නෙමි. පොත් කියවීම හොඳය. ශ්‍රී ලංකාවේ අධ්‍යාපන පද්ධතිය තුළ පවත්නා ව්‍යූහාත්මක වෙනස්කම් සහ ගෝලීයකරණයත් සමඟ ඇතිවී තිබෙන තරඟකාරී ස්වභාවය හේතුවෙන් වර්තමාන ශිෂ්‍ය පරපුර විවිධාකාර අභියෝගයන්ට මුහුණ දී සිටී. අපි හොඳින් ඉගෙන ගනිමු. ගුරුවරුන්ට ගරු කරමු. පාසල පිරිසිදුව තබමු. නවීන තාක්ෂණික මෙවලම් භාවිතය තුළින් අධ්‍යාපන ක්ෂේත්‍රයේ ගුණාත්මක වර්ධනයක් ඇති කිරීම සඳහා රජය විසින් විවිධ ව්‍යාපෘති ක්‍රියාත්මක කරනු ලබන බව පෙනී යයි. දෙමාපියන්ට උදව් කරමු. රටට ආදරය කරමු."""

    try:
        print(f"🚀 Processing single-block paragraph...")
        response = requests.post(URL, json={"text": test_paragraph})
        
        if response.status_code == 200:
            data = response.json()
            
            # Summary of Dynamic Ratio Analysis
            print("\n✅ RATIO ANALYSIS RESULTS:")
            print(f"---------------------------------------------------------------------------")
            print(f"📏 Total Sentences Detected: {data['total_count']}")
            print(f"🚩 Style Anomalies Found:    {data['flagged_count']}")
            print(f"📊 Final Style Change Ratio: {data['style_change_ratio']}%")
            print(f"---------------------------------------------------------------------------")

            # Dynamic Breakdown
            print("\n✍️ SENTENCE-LEVEL BREAKDOWN:")
            for s in data['sentence_data']:
                label = "🚩 [STYLE SHIFT]" if s['is_outlier'] else "[NORMAL]"
                print(f" S{s['id']:<2} | Word Count: {s['length']:<3} | Result: {label}")
            
            print(f"---------------------------------------------------------------------------")
            print(f"Formula Verification: ({data['flagged_count']} / {data['total_count']}) * 100 = {data['style_change_ratio']}%")

        else:
            print(f"❌ Server Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Connection Error: Ensure uvicorn is running.")

if __name__ == "__main__":
    run_single_paragraph_test()