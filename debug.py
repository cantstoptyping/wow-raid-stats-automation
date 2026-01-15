# Create test_wipefest_detailed.py
import requests

report_code = "f3HbJ2whk7CKMaQB"

print("Testing WipeFest API with detailed output...")

url = f"https://www.wipefest.gg/api/report/{report_code}"
print(f"\nURL: {url}")

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"\nRaw Response (first 500 chars):")
    print(response.text[:500])
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\nJSON parsed successfully!")
            print(f"Keys: {data.keys()}")
        except Exception as e:
            print(f"\nFailed to parse JSON: {e}")
    
except Exception as e:
    print(f"Request failed: {e}")

# Also check if the website works
print(f"\n\nYou can manually check:")
print(f"https://www.wipefest.gg/report/{report_code}")
print("If that page loads, the report exists but API might be private/broken")