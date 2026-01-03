from app.rag_chain import load_rag_chain

print("🧪 FINAL TEST of RAG chain compatibility...")

# Load chain
chain = load_rag_chain()

# Test question
test_question = "What are ESRS disclosure requirements?"

print(f"\n❓ Test question: {test_question}")

# Test 1: invoke() method
print("\n🔧 Test 1: Using invoke() method")
try:
    result1 = chain.invoke(test_question)
    print(f"✅ invoke() works!")
    print(f"   Answer preview: {result1.get('result', 'No result')[:200]}...")
    print(f"   Sources: {len(result1.get('source_documents', []))} documents")
except Exception as e:
    print(f"❌ invoke() failed: {e}")

# Test 2: Direct call
print("\n🔧 Test 2: Direct call chain(question)")
try:
    result2 = chain(test_question)
    print(f"✅ Direct call works!")
    print(f"   Answer preview: {result2.get('result', 'No result')[:200]}...")
    print(f"   Sources: {len(result2.get('source_documents', []))} documents")
except Exception as e:
    print(f"❌ Direct call failed: {e}")

# Test 3: Dictionary input
print("\n🔧 Test 3: Dictionary input chain({'query': question})")
try:
    result3 = chain({"query": test_question})
    print(f"✅ Dictionary input works!")
    print(f"   Answer preview: {result3.get('result', 'No result')[:200]}...")
except Exception as e:
    print(f"❌ Dictionary input failed: {e}")

print("\n✅ Test complete!")