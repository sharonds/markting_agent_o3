#!/usr/bin/env python3
"""
Test PR-S adapters with direct API calls to verify credentials
"""
import os
import sys
sys.path.insert(0, '.')

# Set environment
os.environ["PROVIDER_SEARCH"] = "perplexity"
os.environ["PERPLEXITY_API_KEY"] = "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"
os.environ["PERPLEXITY_MODEL"] = "sonar"
os.environ["SEARCH_REGION"] = "EU"
os.environ["SEARCH_LANG"] = "en-GB"

os.environ["PROVIDER_KEYWORDS"] = "dataforseo"
os.environ["DATAFORSEO_LOGIN"] = "sharon@sciammas.com"
os.environ["DATAFORSEO_PASSWORD"] = "07e6c831960825e4"

def test_perplexity_direct():
    """Test Perplexity API directly"""
    import requests
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    model = "sonar"
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a research assistant. Return concise sources with titles and URLs for the query. Region=EU, lang=en-GB"},
            {"role": "user", "content": "marketing automation tools for small businesses"}
        ],
        "max_tokens": 600
    }
    
    try:
        print("🔍 Testing Perplexity API...")
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ API call successful")
            if "choices" in data and data["choices"]:
                content = data["choices"][0]["message"]["content"]
                print(f"Content length: {len(content)}")
                print(f"First 200 chars: {content[:200]}...")
                
                # Check for URLs
                import re
                urls = re.findall(r"https?://\S+", content)
                print(f"URLs found: {len(urls)}")
                for url in urls[:3]:
                    print(f"  - {url}")
            else:
                print("✗ No choices in response")
        else:
            print(f"✗ API error: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")

def test_dataforseo_credentials():
    """Test DataForSEO credentials"""
    import requests
    import base64
    
    login = os.getenv("DATAFORSEO_LOGIN")
    password = os.getenv("DATAFORSEO_PASSWORD")
    
    print("🔍 Testing DataForSEO credentials...")
    
    # Basic auth
    creds = base64.b64encode(f"{login}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}
    
    # Test with a simple API endpoint
    url = "https://api.dataforseo.com/v3/user"
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ DataForSEO credentials valid")
            print(f"Response: {data}")
        else:
            print(f"✗ Credential error: {resp.status_code}")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")

if __name__ == "__main__":
    test_perplexity_direct()
    print()
    test_dataforseo_credentials()
