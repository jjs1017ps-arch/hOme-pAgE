import requests
import base64

def test_elevenlabs():
    api_key_b64 = "Zll6Y1U4V1d2T0R0RVFOUDUzYk5kakxCNW5hN2pESEc6Vm93VGV1dEJFUXJpUEZndGRvYXYzV3VtYlN3WGhVQzFPaHNWSDc5dUhLSTYzMnVBajJZRzd4ZHVZMkw5bDBBWA=="
    try:
        api_key = base64.b64decode(api_key_b64).decode('utf-8')
    except:
        api_key = api_key_b64
    
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": api_key}
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! ElevenLabs API key is valid.")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_elevenlabs()
