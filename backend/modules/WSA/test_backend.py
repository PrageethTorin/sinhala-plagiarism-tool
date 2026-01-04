import requests

URL = "http://127.0.0.1:8000/api/check-wsa"

def run_combined_test():
    test_paragraph = (
        "මානව වංශ ජනනය යනු කිසියම් සමාජ පසුබිමක් තුළ සිටින මිනිසුන් පිරිසක් තමන් වෙනම ජනවාර්ගික කණ්ඩායමක් ලෙස හඳුනා ගන්නා ආකාරයයි. ඊ. පී. තොම්ප්සන් පවසන ආකාරයට, මෙම ක්‍රියාවලිය හරහා විවිධ ජන වර්ග තමන්ගේම අනන්‍යතාවයක් ගොඩනගා ගනිමින් ඉතිහාසයට එක් වෙති. මේ නිසා, කලින් ඓතිහාසික කරුණු ලෙස සැලකූ සමහර පැරණි කතා දැන් බොහෝ දෙනෙක් දකින්නේ ජනප්‍රවාද ලෙසටයි."
   )

    try:
        response = requests.post(URL, json={"text": test_paragraph})
        data = response.json()
        
        if 'style_change_ratio' in data:
            print("="*80)
            print("✅ DUAL-METRIC RESEARCH ANALYSIS (STYLE & INTERNET DISCOVERY)")
            print(f"📊 Style Change Ratio: {data['style_change_ratio']}%")
            print(f"🔗 BEST SAME IDEA URL: {data.get('matched_url', 'No source found')}")
            print("-" * 80)
            print(f"{'ID':<4} | {'Len':<5} | {'TTR %':<10} | {'Status'}")
            print("-" * 60)
            
            for s in data['sentence_map']:
                status = "🚩 STYLE SHIFT" if s['is_outlier'] else "✓ Baseline"
                print(f"S{s['id']:<3} | {s['length']:<5} | {s['lexical_ttr']:<10} | {status}")
            print("-" * 80)
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    run_combined_test()