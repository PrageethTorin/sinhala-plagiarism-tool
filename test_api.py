import subprocess
import json
import sys

result = subprocess.run([
    sys.executable, "-m", "pip", "show", "requests"
], capture_output=True, text=True)

if result.returncode != 0:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])

import requests

url = "http://127.0.0.1:8000/api/plagiarism/analyze-file"
# Test with EXACT corpus text - should show PLAGIARIZED
test_text = "1917 ඔක්‌තෝබර් විප්ලවයෙන් පසු අධිරාජ්‍යවාදීහු සහ බලයෙන් පහ කරන ලද ධනේශ්වර පංතිය හා ඉඩම් හිමියෝ රුසියාවේ කම්කරුවන්ගේ හා ගොවීන්ගේ ජයග්‍රහණය පිළිගැනීම ප්‍රතික්‌ෂේප කළෝය"

try:
    print("Testing /analyze-file with EXACT corpus text...", file=sys.stderr)
    sys.stderr.flush()
    
    files = {"text": (None, test_text)}
    response = requests.post(url, files=files, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        # Just show the key metrics
        print("\n=== PLAGIARISM DETECTION RESULTS ===", file=sys.stdout)
        print(f"Overall Score:  {result['overall']}%", file=sys.stdout)
        print(f"Decision:       {result['decision']}", file=sys.stdout)
        print(f"Fallback Used:  {result.get('used_fallback', False)}", file=sys.stdout)
        print(f"\n3 Metrics Breakdown:", file=sys.stdout)
        print(f"  - Semantic Similarity:    {result['features']['semantic']}%", file=sys.stdout)
        print(f"  - Paraphrase Detection:   {result['features']['paraphrase']}%", file=sys.stdout)
        print(f"  - Writing Style Analysis: {result['features']['style']}%", file=sys.stdout)
    else:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)
        
except Exception as e:
    import traceback
    print(f"Error: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
