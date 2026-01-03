#!/usr/bin/env python3
"""
Test Google Gemini integration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Check if API key exists
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    print(f"✅ Found API key: {api_key[:15]}...")
    
    # Test Gemini directly
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content("What is ESG in one sentence?")
        print(f"✅ Gemini test successful!")
        print(f"Response: {response.text}")
        
        # Now test our RAG chain
        print("\n🧪 Testing RAG chain with AI...")
        from rag_chain import load_rag_chain
        chain = load_rag_chain(use_ai=True)
        result = chain.invoke("Compare ESRS and GRI standards")
        print(f"✅ RAG chain works!")
        print(f"Answer length: {len(result['result'])} chars")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
else:
    print("❌ No GEMINI_API_KEY found in .env file")
    print("\n📝 Get your key:")
    print("1. Visit: https://makersuite.google.com/app/apikey")
    print("2. Click 'Create API Key'")
    print("3. Copy the key")
    print("4. Add to .env file: GEMINI_API_KEY=your_key_here")