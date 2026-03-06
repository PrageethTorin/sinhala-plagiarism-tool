#!/usr/bin/env python3
"""
Test to verify the backend returns data in correct format for frontend
"""
import requests
import json
import time

SERVER_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{SERVER_URL}/api/check-wsa"

def test_response_format():
    """Test the response format matches frontend expectations"""
    print("\n" + "=" * 70)
    print("TESTING BACKEND RESPONSE FORMAT")
    print("=" * 70)
    
    test_data = {
        "text": "අධිකරණ ක්‍රියාවලිය අතිශයින්ම වැදගත්ය. නිතිය ගරු කිරීම සමාජයේ පදනම."
    }
    
    print(f"\n📤 Sending request to: {ENDPOINT}")
    print(f"📝 Test text: {test_data['text']}\n")
    
    try:
        response = requests.post(
            ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ Response received successfully!")
            print("\n📊 Response Structure:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Check for the expected structure
            print("\n✓ Checking response format...\n")
            
            checks = [
                ("Has 'ratio_data'", 'ratio_data' in result),
                ("Has 'style_change_ratio'", 'style_change_ratio' in result.get('ratio_data', {})),
                ("Has 'matched_url'", 'matched_url' in result.get('ratio_data', {})),
                ("Has 'similarity_score'", 'similarity_score' in result.get('ratio_data', {})),
                ("Has 'sentence_map'", 'sentence_map' in result.get('ratio_data', {})),
            ]
            
            all_passed = True
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"  {status} {check_name}")
                if not check_result:
                    all_passed = False
            
            if all_passed:
                print("\n✅ Response format is CORRECT for frontend!")
                print("The analysis button output should now display properly.")
                return True
            else:
                print("\n❌ Response format MISMATCH!")
                print("Frontend may not display results correctly.")
                return False
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running")
        print("Start server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n🔍 Verifying Backend Response Format for Frontend\n")
    
    # Wait for server
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    success = test_response_format()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ BACKEND RESPONSE FORMAT IS CORRECT")
        print("=" * 70)
        print("\nAction: The frontend should now display analysis results!")
        print("\nNext steps:")
        print("1. Open frontend in browser")
        print("2. Navigate to Writing Style Analysis")
        print("3. Enter Sinhala text and click 'Analyze Style'")
        print("4. Results should now display below the button")
    else:
        print("⚠️ RESPONSE FORMAT ISSUE")
        print("=" * 70)
        print("\nAction: Check backend response format")
    print()
