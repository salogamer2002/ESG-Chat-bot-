"""
RAG CHAIN WITH FIREWORKS AI - FULL RESPONSE VERSION
No token limits - AI gives complete answers for all queries
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class ESGKnowledgeBase:
    """Local ESG knowledge base"""
    
    @staticmethod
    def get_local_answer(question):
        """Return basic ESG answers"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["esrs", "european sustainability"]):
            return """**📊 ESRS (European Sustainability Reporting Standards)**

**Key Requirements:**
- Environmental disclosures (climate, pollution, water, biodiversity)
- Social disclosures (workforce, supply chain, communities)
- Governance disclosures (ethics, anti-corruption)
- Digital reporting format (XHTML)
- Limited assurance requirement
- Applies to large EU companies from 2024"""
        
        elif any(word in question_lower for word in ["gri", "global reporting"]):
            return """**🌍 GRI Standards**

**Structure:**
- Universal standards (GRI 101, 102, 103)
- Topic standards (200: Economic, 300: Environmental, 400: Social)
- Used by 15,000+ organizations globally
- Stakeholder-focused reporting"""
        
        elif any(word in question_lower for word in ["csrd", "corporate sustainability"]):
            return """**🇪🇺 CSRD (Corporate Sustainability Reporting Directive)**

**Scope:**
- Large EU companies (250+ employees, €40M+ turnover)
- Listed SMEs
- Non-EU companies with significant EU operations
- Phased implementation 2024-2028"""
        
        elif any(word in question_lower for word in ["esg", "environmental social governance"]):
            return """**📈 ESG Framework**

**Components:**
- Environmental: Climate, resources, pollution
- Social: Labor, diversity, human rights
- Governance: Ethics, transparency, risk management

**Benefits:**
- Risk mitigation
- Cost savings
- Investor attraction
- Regulatory compliance"""
        
        else:
            return """**🤖 ESG Compliance Assistant**

I can help with:
- ESRS (European Sustainability Reporting Standards)
- GRI (Global Reporting Initiative)
- CSRD (Corporate Sustainability Reporting Directive)
- SASB (Sustainability Accounting Standards Board)
- General ESG compliance

Ask me anything about ESG!"""

class FireworksAIAssistant:
    """Fireworks AI integration with Kimi K2 Instruct model"""
    
    def __init__(self, api_key=None):
        try:
            # Get API key from environment or parameter
            self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
            
            if not self.api_key:
                print("⚠️ FIREWORKS_API_KEY not found. Using local knowledge only.")
                print("   Get key from: https://fireworks.ai/")
                print("   Add to .env file: FIREWORKS_API_KEY=your_key_here")
                self.available = False
                return
            
            # Fireworks AI configuration
            self.url = "https://api.fireworks.ai/inference/v1/chat/completions"
            self.model = "accounts/fireworks/models/kimi-k2-instruct-0905"
            self.available = True
            print("✅ Fireworks AI (Kimi K2) Connected")
            
        except Exception as e:
            print(f"❌ Fireworks AI setup failed: {e}")
            self.available = False
    
    def enhance_answer(self, question, local_answer=None):
        """Get AI response (with or without local answer) - FULL LENGTH"""
        if not self.available:
            return local_answer or "I'm currently running without AI assistance. Please ask about ESRS, GRI, CSRD, or other ESG topics for detailed information."
        
        try:
            # ✨ REMOVED OPTIMIZATION - Always use full token limit
            max_tokens = 4096  # Full response for ALL queries
            temperature = 0.6
            print(f"🚀 Using full AI response (max_tokens={max_tokens})")
            
            # Prepare different prompts based on whether we have local answer
            if local_answer:
                # Enhance existing answer
                prompt = f"""You are an ESG (Environmental, Social, Governance) compliance expert. 
Enhance the following answer with more details and practical insights.

QUESTION: {question}

CURRENT ANSWER: {local_answer}

Please add:
1. Recent updates (2023-2024 regulations)
2. Practical implementation examples
3. Industry-specific considerations
4. Common challenges and solutions
5. Best practices from leading companies

Keep the tone professional and focused on compliance requirements.
Structure the answer clearly with headings and bullet points where helpful."""
            else:
                # Generate complete response for ANY question
                prompt = f"""You are a friendly and knowledgeable ESG (Environmental, Social, Governance) compliance expert assistant.

User's question: {question}

Please respond naturally and professionally with a COMPLETE answer. If it's a greeting or casual question, be friendly and welcoming while introducing yourself as an ESG compliance assistant. If it's an ESG-related question, provide detailed, accurate information about sustainability reporting standards, compliance requirements, and best practices.

You specialize in:
- ESRS (European Sustainability Reporting Standards)
- GRI (Global Reporting Initiative)
- CSRD (Corporate Sustainability Reporting Directive)
- SASB (Sustainability Accounting Standards Board)
- ESG compliance and implementation

Respond in a helpful, conversational tone. Give a thorough, complete answer."""

            # Prepare request payload - Fireworks AI format
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "top_p": 1,
                "top_k": 40,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Make API request with timeout
            print(f"⏳ Calling Fireworks AI (timeout: 90s)...")
            response = requests.request(
                "POST",
                self.url,
                headers=headers,
                data=json.dumps(payload),
                timeout=90  # Increased timeout for longer responses
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                print(f"✅ AI response received ({len(ai_response)} chars)")
                
                # Return formatted response based on type
                if local_answer:
                    return f"""{local_answer}

---

**🤖 AI-Enhanced Insights:**
{ai_response}"""
                else:
                    return ai_response
            else:
                print(f"⚠️ Fireworks AI error {response.status_code}: {response.text}")
                return local_answer or "I'm currently experiencing technical difficulties. Please try again or ask about specific ESG topics."
            
        except requests.exceptions.Timeout:
            print("⚠️ AI request timeout (90s exceeded) - using local answer")
            print("   This might be a network issue. Try again or check your connection.")
            return local_answer
        except Exception as e:
            print(f"⚠️ AI enhancement failed: {e}")
            import traceback
            traceback.print_exc()
            return local_answer


class AIEnhancedRAGChain:
    """Hybrid RAG chain with local knowledge + Fireworks AI enhancement"""
    
    def __init__(self, use_ai=True):
        self.local_kb = ESGKnowledgeBase()
        self.use_ai = use_ai
        
        if use_ai:
            self.ai_assistant = FireworksAIAssistant()
        else:
            self.ai_assistant = None
            print("ℹ️ Running in local-only mode")
    
    def get_answer(self, question):
        """Get enhanced answer - ALWAYS use AI with FULL responses"""
        # Get local answer first (may be None for casual questions)
        local_answer = self.local_kb.get_local_answer(question)
        
        # ALWAYS use AI if it's available
        should_use_ai = (
            self.use_ai and 
            self.ai_assistant and 
            self.ai_assistant.available
        )
        
        if should_use_ai:
            if local_answer is None:
                print(f"🤖 Using AI for complete response...")
            else:
                print(f"🤖 Using AI to enhance answer...")
            
            # Get FULL AI response (no optimization)
            return self.ai_assistant.enhance_answer(question, local_answer)
        
        # Fallback to local answer or default message
        return local_answer or """**🤖 ESG Compliance Assistant**

I can help with:
- ESRS (European Sustainability Reporting Standards)
- GRI (Global Reporting Initiative)
- CSRD (Corporate Sustainability Reporting Directive)
- SASB (Sustainability Accounting Standards Board)
- General ESG compliance

Ask me anything about ESG!"""


class RAGChainWrapper:
    """Wrapper for Chainlit compatibility"""
    
    def __init__(self, use_ai=True):
        self.chain = AIEnhancedRAGChain(use_ai=use_ai)
        print("✅ Fireworks AI-Enhanced RAG Chain Ready (Full Response Mode)")
    
    def invoke(self, inputs):
        """Handle all input types"""
        # Extract question
        if isinstance(inputs, str):
            question = inputs
        elif isinstance(inputs, dict):
            question = inputs.get("query") or inputs.get("question") or str(inputs)
        else:
            question = str(inputs)
        
        print(f"🔍 Processing: {question[:50]}...")
        
        # Get answer
        answer = self.chain.get_answer(question)
        
        # Return in expected format
        return {
            "query": question,
            "result": answer,
            "source_documents": []
        }
    
    def __call__(self, inputs):
        return self.invoke(inputs)


def load_rag_chain(use_ai=True):
    """Load the RAG chain with optional Fireworks AI enhancement"""
    print(f"🚀 Loading {'Fireworks AI-Enhanced ' if use_ai else ''}RAG Chain (Full Response Mode)...")
    return RAGChainWrapper(use_ai=use_ai)


def load_gap_analysis_chain(use_ai=True):
    """Load gap analysis chain"""
    return load_rag_chain(use_ai=use_ai)


# Test function
if __name__ == "__main__":
    print("🧪 Testing Fireworks AI-Enhanced RAG Chain (Full Response Mode)...")
    print("=" * 60)
    
    # Test with Fireworks AI
    chain_ai = load_rag_chain(use_ai=True)
    
    test_questions = [
        "hi",
        "What are ESRS disclosure requirements?",
        "Compare GRI and SASB standards",
        "How to implement ESG compliance in manufacturing?",
        "What are recent updates in EU sustainability regulations?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. ❓ Question: {question}")
        result = chain_ai.invoke(question)
        print(f"   ✅ Answer ready ({len(result['result'])} chars)")
        
        # Check if AI was used
        if "AI-Enhanced Insights:" in result['result']:
            print("   🤖 AI Enhancement: Yes (Enhanced)")
        elif len(result['result']) > 500:
            print("   🤖 AI Enhancement: Yes (Fresh AI response)")
        else:
            print("   🤖 AI Enhancement: No (using local knowledge)")
        
        print(f"   Preview: {result['result'][:150]}...")
    
    print("\n" + "=" * 60)
    print("🎉 Testing Complete!")
    print("\n📝 Setup Instructions:")
    print("1. Get API key: https://fireworks.ai/")
    print("2. Add to .env file: FIREWORKS_API_KEY=your_key_here")
    print("3. Restart the app")
    print("\n🔥 AI now gives FULL, complete responses for ALL queries!")