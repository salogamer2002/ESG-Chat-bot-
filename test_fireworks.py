#!/usr/bin/env python3
"""
Test Fireworks AI integration
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_fireworks_direct():
    """Test Fireworks API directly"""
    api_key = os.getenv("FIREWORKS_API_KEY")
    
    if not api_key:
        print("❌ No FIREWORKS_API_KEY found in .env file")
        print("\n📝 Setup:")
        print("1. Visit: https://fireworks.ai/")
        print("2. Sign up and get API key")
        print("3. Add to .env file: FIREWORKS_API_KEY=your_key_here")
        return False
    
    print(f"✅ Found API key: {api_key[:15]}...")
    
    try:
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        
        payload = {
            "model": "accounts/fireworks/models/kimi-k2-instruct-0905",
            "max_tokens": 4096,  # Max without streaming (>4096 requires stream=true)
            "top_p": 1,
            "top_k": 40,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "temperature": 0.6,
            "messages": [
                {
                    "role": "user",
                    "content": "What is ESG in one sentence?"
                }
            ]
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        print("🔄 Testing Fireworks AI API...")
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"✅ Fireworks AI test successful!")
            print(f"Response: {answer}")
            return True
        else:
            print(f"❌ API Error {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_rag_chain():
    """Test RAG chain with Fireworks AI"""
    try:
        print("\n🧪 Testing RAG chain with Fireworks AI...")
        from app.rag_chain import load_rag_chain
        
        chain = load_rag_chain(use_ai=True)
        result = chain.invoke("Compare ESRS and GRI standards")
        
        print(f"✅ RAG chain works!")
        print(f"Answer length: {len(result['result'])} chars")
        
        if "AI-Enhanced Insights:" in result['result']:
            print("✅ AI enhancement working!")
        else:
            print("ℹ️ Using local knowledge only")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG chain test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 FIREWORKS AI INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Direct API
    api_works = test_fireworks_direct()
    
    # Test 2: RAG Chain
    if api_works:
        test_rag_chain()
    
    print("\n" + "=" * 60)
    print("✅ Testing Complete!")
    print("=" * 60)