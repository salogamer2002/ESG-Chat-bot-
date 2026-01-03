import subprocess
import sys
import os

print("🚀 Setting up Ollama for ESG Chatbot...")
print("=" * 50)

# Check if Ollama is installed
try:
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    print(f"✅ Ollama is installed: {result.stdout.strip()}")
except:
    print("❌ Ollama not found. Please install from: https://ollama.com/")
    print("   After installing, run this script again.")
    sys.exit(1)

# Pull recommended model
models = ["llama3.2", "mistral", "phi3"]
for model in models:
    print(f"\n🔄 Checking for {model}...")
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    
    if model in result.stdout:
        print(f"✅ {model} already downloaded")
    else:
        print(f"📥 Downloading {model} (this may take a few minutes)...")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"✅ Successfully downloaded {model}")
            break  # Stop after first successful download
        except Exception as e:
            print(f"❌ Failed to download {model}: {e}")
            continue

print("\n" + "=" * 50)
print("🎉 Setup complete! Now run:")
print("chainlit run chainlit_callbacks.py")