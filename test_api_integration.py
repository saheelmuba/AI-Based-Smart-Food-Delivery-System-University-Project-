"""
Comprehensive API Test Suite for AI Food Delivery System
Tests voice, image, and recommendation integration
"""
import json
import urllib.request
import urllib.error
import base64

BASE_URL = "http://127.0.0.1:5002"
HEALTH_URL = f"{BASE_URL}/health"

def test_health():
    """Test basic health endpoint"""
    print("=" * 60)
    print("TEST: Health Check")
    print("=" * 60)
    try:
        req = urllib.request.Request(HEALTH_URL)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✓ Health: {response.status}")
            print(f"✓ Response: {json.dumps(data, indent=2)}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_menu_items():
    """Test menu items endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Menu Items (Public)")
    print("=" * 60)
    try:
        url = f"{BASE_URL}/api/menu/items"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✓ Menu Items: {response.status}")
            if isinstance(data, list):
                print(f"✓ Found {len(data)} items")
                if data:
                    print(f"✓ Sample item: {json.dumps(data[0], indent=2)}")
            else:
                print(f"✓ Response: {json.dumps(data, indent=2)}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_analytics_dashboard():
    """Test analytics dashboard endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Analytics Dashboard (Public)")
    print("=" * 60)
    try:
        url = f"{BASE_URL}/api/analytics/dashboard"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✓ Analytics Dashboard: {response.status}")
            print(f"✓ Response: {json.dumps(data, indent=2)}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_auth_registration():
    """Test user registration"""
    print("\n" + "=" * 60)
    print("TEST: User Registration")
    print("=" * 60)
    try:
        url = f"{BASE_URL}/api/auth/register"
        payload = {
            "email": f"test_user_{hash('test') % 10000}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode())
                print(f"✓ Registration: {response.status}")
                print(f"✓ Response: {json.dumps(result, indent=2)}")
                return result.get('access_token'), result.get('user_id')
        except urllib.error.HTTPError as e:
            if e.code == 409:
                print(f"⚠ User already exists (409)")
                # Try login instead
                return test_auth_login()
            raise
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None

def test_auth_login():
    """Test user login"""
    print("\n" + "=" * 60)
    print("TEST: User Login")
    print("=" * 60)
    try:
        url = f"{BASE_URL}/api/auth/login"
        payload = {
            "email": "test@example.com",
            "password": "password123"
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"✓ Login: {response.status}")
            print(f"✓ Response: {json.dumps(result, indent=2)}")
            return result.get('access_token'), result.get('user_id')
    except urllib.error.HTTPError as e:
        print(f"✗ Login failed: {e.code}")
        return None, None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None

def test_voice_transcribe(token):
    """Test voice transcription endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Voice Transcription (Requires Auth)")
    print("=" * 60)
    if not token:
        print("⚠ Skipped: No authentication token")
        return False
    try:
        url = f"{BASE_URL}/api/voice/transcribe"
        payload = {"transcript": "add pizza to my order"}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"✓ Voice Transcribe: {response.status}")
            print(f"✓ Command: {result.get('command')}")
            print(f"✓ Details: {result.get('details')}")
            print(f"✓ Message: {result.get('message')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"✗ Error: {e.code} {e.reason}")
        if e.code == 401:
            print("  (Authentication required)")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_image_recognition(token):
    """Test image recognition endpoint"""
    print("\n" + "=" * 60)
    print("TEST: Image Recognition (Requires Auth)")
    print("=" * 60)
    if not token:
        print("⚠ Skipped: No authentication token")
        return False
    try:
        # Create a simple test image (1x1 white PNG)
        png_data = base64.b64decode(
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='
        )
        
        boundary = '----WebKitFormBoundary'
        body = (
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
            'Content-Type: image/png\r\n\r\n'
        ).encode() + png_data + f'\r\n--{boundary}--\r\n'.encode()
        
        url = f"{BASE_URL}/api/image/upload"
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Authorization': f'Bearer {token}'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"✓ Image Upload: {response.status}")
            print(f"✓ Analysis: {result.get('analysis')}")
            print(f"✓ Matched Items: {result.get('matched')}")
            print(f"✓ Suggestions: {result.get('suggestions')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"✗ Error: {e.code} {e.reason}")
        if e.code == 401:
            print("  (Authentication required)")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_ai_recommendation(token):
    """Test AI recommendation endpoint"""
    print("\n" + "=" * 60)
    print("TEST: AI Recommendation (Requires Auth)")
    print("=" * 60)
    if not token:
        print("⚠ Skipped: No authentication token")
        return False
    try:
        url = f"{BASE_URL}/api/ai/recommend"
        payload = {"prompt": "vegetarian lunch options"}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"✓ Recommendation: {response.status}")
            print(f"✓ Response: {json.dumps(result, indent=2)}")
            return True
    except urllib.error.HTTPError as e:
        print(f"✗ Error: {e.code} {e.reason}")
        if e.code == 401:
            print("  (Authentication required)")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + "  AI FOOD DELIVERY SYSTEM - API INTEGRATION TEST  ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Test public endpoints
    health_ok = test_health()
    menu_ok = test_menu_items()
    analytics_ok = test_analytics_dashboard()
    
    # Test authentication and protected endpoints
    token, user_id = test_auth_registration()
    if not token:
        token, user_id = test_auth_login()
    
    # Test voice and image
    voice_ok = test_voice_transcribe(token)
    image_ok = test_image_recognition(token)
    ai_ok = test_ai_recommendation(token)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    summary = {
        "Public Endpoints": {
            "Health": "✓" if health_ok else "✗",
            "Menu Items": "✓" if menu_ok else "✗",
            "Analytics Dashboard": "✓" if analytics_ok else "✗"
        },
        "Protected Endpoints": {
            "Voice Transcribe": "✓" if voice_ok else "✗",
            "Image Recognition": "✓" if image_ok else "✗",
            "AI Recommendation": "✓" if ai_ok else "✗"
        }
    }
    print(json.dumps(summary, indent=2))
    print("=" * 60)
