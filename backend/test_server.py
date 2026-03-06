#!/usr/bin/env python3
"""
Quick test to verify the fix works - run this after starting the server
"""
import requests
import json
import time

# Test configuration
SERVER_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{SERVER_URL}/api/check-wsa"

def test_server():
    """Test the WSA endpoint"""
    print("\n" + "=" * 70)
    print("TESTING SINHALA PLAGIARISM DETECTION SERVER")
    print("=" * 70)
    
    # Wait a moment for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test data in Sinhala
    test_text = """
    අධිකරණ ක්‍රියාවලිය අතිශයින්ම වැදගත්ය. නිතිය ගරු කිරීම සමාජයේ අඩිතාලම ඇස්ගන්නා කරුණු. 
    අපේ ගිණුම්ගතයි නිතිගත ප්‍රක්‍රියා අනුගමනය කිරීම. ප්‍රතිසංස්කරණ ක්‍රියාවලිය පිරිසිදු විය යුතුය.
    """
    
    payload = {
        "text": test_text
    }
    
    print(f"\n📤 Sending request to: {ENDPOINT}")
    print(f"📝 Test text length: {len(test_text)} characters")
    
    try:
        # Send POST request
        response = requests.post(
            ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Server is working correctly")
            result = response.json()
            print("\n📊 Analysis Results:")
            print(f"  - Style Change Ratio: {result.get('style_change_ratio', 'N/A')}%")
            print(f"  - Similarity Score: {result.get('similarity_score', 'N/A')}%")
            print(f"  - Matched URL: {result.get('matched_url', 'N/A')}")
            print(f"  - Sentences Analyzed: {len(result.get('sentence_map', []))}")
            return True
        else:
            print(f"❌ ERROR! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print("   Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_server()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 PLAGIARISM DETECTION TOOL IS WORKING!")
        print("=" * 70)
        print("\nServer is ready to accept plagiarism detection requests.")
    else:
        print("⚠️ TEST FAILED")
        print("=" * 70)
        print("\nPlease check that:")
        print("1. Server is running: python main.py")
        print("2. Port 8000 is not being used by another process")
        print("3. All dependencies are installed")
    print()
