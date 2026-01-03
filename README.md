# 🌍 ESG Compliance Chatbot – Project Mīzān

A secure, Retrieval-Augmented Generation (RAG) based chatbot that helps **SMEs** understand and comply with **Environmental, Social, and Governance (ESG)** regulations. This AI assistant can parse legal texts, extract region-specific requirements, and answer complex compliance questions—all while being completely open-source, cloud-agnostic, and self-hostable.

---

## 📌 Key Features

- ✅ **RAG-based chatbot** for interactive, accurate legal Q&A
- 📂 Ingests and indexes ESG documents in nested folders (~5.6 GB tested)
- 🔎 Uses FAISS for fast, similarity-based retrieval
- 🧠 LangChain-powered orchestration with OpenAI GPT-3.5 Turbo
- 📊 Embedded legal advisory prototype (rules engine-ready)
- 💬 Built-in **Chainlit** chat interface (real-time)
- 📝 **Profile capture system**: Collects user data (name, org, country) on first login
- 📄 **Document upload & ESG gap analysis** with page-level scoring and recommendations
- 📎 Source-linked answers with PDF URLs (chunk-aware)
- 🔐 Zero vendor lock-in, local or private cloud deployable

---

## 🧠 System Architecture

| Component            | Technology / Description                                              |
|----------------------|----------------------------------------------------------------------|
| **Embedding Model**  | `all-MiniLM-L6-v2` via SentenceTransformers                         |
| **Vector Store**     | FAISS (`IndexHNSWFlat`, 384-dim embeddings)                          |
| **LLM**              | OpenAI GPT-3.5 Turbo (API-based)                                     |
| **Retriever**        | Custom LangChain retriever (top-k=5)                                 |
| **Frontend**         | Chainlit (WebSocket UI for chat + profile handling)                  |
| **Chunking**         | Token-aware using `tiktoken` (max 512 tokens per chunk)              |
| **Gap Analysis**     | Async section-level report generation with compliance scoring        |
| **Storage**          | Filesystem (or MinIO for scalable deployments)                       |
| **Orchestration**    | Docker (dev), Kubernetes via K3s/MicroK8s (prod ready)               |

---

## 🧾 Documented Use Cases

- “What is the minimum wage in Bangladesh?”
- “Is maternity leave mandatory in Jordan?”
- “Do we have to disclose worker audits under Saudi ESG rules?”
- “What counts as forced labor under ILO conventions?”
- “Upload this policy and give a gap analysis”

---

## 📁 Directory Layout

```

esg-chatbot/
├── app/
│ ├── ingest.py # Recursively loads ESG documents from nested folders
│ ├── embed.py # Embeds documents & builds FAISS index
│ ├── rag_chain.py # Constructs LangChain RetrievalQA chain
│ ├── user_db.py # Manages user profile database (SQLite)
│ ├── file_analysis.py # Gap analysis engine for uploaded PDFs/DOCX
│ └── utils.py # Token-aware text chunking
├── data/
│ └── raw_docs/ # Store original ESG PDFs and documents
├── vector_store/ # Persisted FAISS index
├── chainlit_app.py # Frontend interface with Chainlit
├── requirements.txt # All Python dependencies
└── .env # OpenAI API key (secured)

````

---

## 📦 Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/rawahabinkhalid/esg-chatbot.git
cd esg-chatbot
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=sk-your-openai-key-here

# 🌐 OAuth for Google Sign-In (Chainlit)
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH_GOOGLE_CLIENT_SECRET=your-google-client-secret

# 📊 Optional: Literal API Key (for observability if integrated)
LITERAL_API_KEY=your-literal-api-key

# 🔐 Chainlit Auth (used for secure sessions)
CHAINLIT_AUTH_SECRET=your-random-secret-string

# 🌍 Public-facing chatbot URL (used for profile completion redirect & file links)
URL="https://chat.mizan-ai.com"
```

### 4. Add Your ESG Documents

Place all your ESG files (PDFs, DOCX, TXT) inside:

```
data/raw_docs/
```

Nested directories are fully supported.

---

## 🔧 Preprocessing & Embedding

### Chunking Strategy

* Rule-based with fallback on token count.
* Uses `tiktoken` tokenizer to ensure chunks ≤ 512 tokens.
* Chunk metadata includes file path, chunk number, and source.

### Embedding Strategy

* Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
* Vector index: `faiss.IndexHNSWFlat(dim=384, M=32)`
* Metadata stored: `{"source": filepath, "chunk": i}`

### Run Embedding Pipeline

```bash
python -c "from app.embed import embed_documents; embed_documents()"
python -c "from app.embed import add_single_document_to_faiss; add_single_document_to_faiss('mizan-training-sources.md')"
```

This will build a FAISS index at `vector_store/faiss_index`.

---

## 💬 Start the Chatbot UI

```bash
uvicorn asgi_app:app --host 0.0.0.0 --port 8000
```

Visit: [https://chat.mizan-ai.com](https://chat.mizan-ai.com)

---

## 🧪 Example Prompts to Try

* “What are the working hours laws in Jordan?”
* “What audit disclosures are required by EU supply chain laws?”
* “Does Bangladesh mandate grievance redressal mechanisms?”
* “Give maternity leave duration under Saudi ESG guidelines.”
* “Analyze this uploaded ESG report for compliance issues.”

---

## 🧱 Component Details

### `app/ingest.py`

* Walks through all folders under `data/raw_docs`
* Loads `.pdf`, `.docx`, and `.txt` files
* Extracts text using `PyMuPDF`

### `app/utils.py`

* Breaks down documents into 512-token chunks
* Tokenizer-aware (ensures model compatibility)
* Returns list of clean, context-preserving text chunks

### `app/embed.py`

* Embeds documents using `SentenceTransformers`
* Stores vector data and metadata in local FAISS DB
* Callable standalone from any script

### `app/rag_chain.py`

* Loads FAISS index
* Uses LangChain to construct a RetrievalQA chain
* Injects prompt template with:

  * Top-k context
  * User query
  * Section-citing instruction

### `app/file_analysis.py`

* Performs ESG gap analysis using GPT-3.5
* Breaks documents into page-based chunks
* Evaluates strengths, gaps, improvements, and confidence levels
* Produces detailed final compliance summary

### `chainlit_app.py`

* Handles OAuth login and enforces profile completion
* Connects RAG engine and document evaluator to Chainlit
* Handles chat events via Chainlit
* On user message, runs the LangChain RAG chain
* Streams response back in real-time
* Logs conversations with source metadata

---

## 🧠 Prompt Template

```text
You are a compliance assistant for ESG regulations.

User Question: {question}

Relevant legal content:
{context}

Instructions: Answer using only the legal context, cite section where possible.
```

---

## 🛡️ Security & Hosting

* ✅ Self-hostable (no AWS/GCP required)
* 🔒 API keys are environment-protected
* 🧾 Optional integration with MinIO for scalable object storage
* 🧍‍♂️ Local-only inference options possible with vLLM or llama.cpp (future)
* 🛑 Prompts users not to share sensitive information
* ✅ Logs stored securely (JSONL format by date)

---

## 🔭 Roadmap

| Week | Focus                       | Goals                                       |
| ---- | --------------------------- | ------------------------------------------- |
| 6    | RAG Output Tuning           | Score ranking, pruning long responses       |
| 7    | Advisory Engine Integration | Rule-based YAML/JSON DSL-based suggestions  |
| 8    | UI Feedback & Finalization  | Streamed answers, user feedback logging     |
| 9+   | Beta Test with SMEs         | Iterative testing, multilingual enhancement |

---

## 🔌 Optional Enhancements

* Stream answers word-by-word using OpenAI streaming API
* Add authentication + per-user FAISS filtering
* Visual summaries or charts (ESG scoring)
* Admin dashboard for auditing chatbot responses
#   E S G - C h a t - b o t -  
 