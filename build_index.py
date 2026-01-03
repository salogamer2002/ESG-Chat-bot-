import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Fixed import
import glob

def load_documents(data_dir="data/raw_docs"):
    """Load all documents from the data directory."""
    documents = []
    
    # Check if directory exists
    if not os.path.exists(data_dir):
        print(f"❌ Directory {data_dir} does not exist!")
        print(f"Creating directory and adding sample document...")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create a sample document
        sample_file = os.path.join(data_dir, "sample_esg_doc.txt")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("""
ESG Compliance Guide

Environmental Standards:
- Companies must report carbon emissions annually
- Waste management protocols must be documented
- Water usage must be monitored and reported

Social Responsibility:
- Fair labor practices must be maintained
- Worker safety standards must be met
- Diversity and inclusion policies required

Governance:
- Board diversity requirements
- Transparent reporting standards
- Ethical business practices
""")
        print(f"✅ Created sample document: {sample_file}")
    
    # Load PDF files
    pdf_files = glob.glob(os.path.join(data_dir, "**/*.pdf"), recursive=True)
    for pdf_file in pdf_files:
        try:
            loader = PyPDFLoader(pdf_file)
            documents.extend(loader.load())
            print(f"✅ Loaded PDF: {pdf_file}")
        except Exception as e:
            print(f"❌ Error loading {pdf_file}: {e}")
    
    # Load text files
    txt_files = glob.glob(os.path.join(data_dir, "**/*.txt"), recursive=True)
    for txt_file in txt_files:
        try:
            loader = TextLoader(txt_file, encoding="utf-8")
            documents.extend(loader.load())
            print(f"✅ Loaded TXT: {txt_file}")
        except Exception as e:
            print(f"❌ Error loading {txt_file}: {e}")
    
    # Load Word documents
    doc_files = glob.glob(os.path.join(data_dir, "**/*.docx"), recursive=True)
    for doc_file in doc_files:
        try:
            loader = UnstructuredWordDocumentLoader(doc_file)
            documents.extend(loader.load())
            print(f"✅ Loaded DOCX: {doc_file}")
        except Exception as e:
            print(f"❌ Error loading {doc_file}: {e}")
    
    # Load CSV files
    csv_files = glob.glob(os.path.join(data_dir, "**/*.csv"), recursive=True)
    for csv_file in csv_files:
        try:
            loader = CSVLoader(csv_file, encoding="utf-8")
            documents.extend(loader.load())
            print(f"✅ Loaded CSV: {csv_file}")
        except Exception as e:
            print(f"❌ Error loading {csv_file}: {e}")
    
    # Load Markdown files
    md_files = glob.glob(os.path.join(data_dir, "**/*.md"), recursive=True)
    for md_file in md_files:
        try:
            loader = TextLoader(md_file, encoding="utf-8")
            documents.extend(loader.load())
            print(f"✅ Loaded MD: {md_file}")
        except Exception as e:
            print(f"❌ Error loading {md_file}: {e}")
    
    return documents

def build_vector_store(
    data_dir="data/raw_docs",
    output_dir="vector_store/faiss_index",
    chunk_size=1000,
    chunk_overlap=200
):
    """Build FAISS vector store from documents."""
    
    print("\n" + "="*50)
    print("Building FAISS Vector Store")
    print("="*50 + "\n")
    
    # Load documents
    print("📂 Loading documents...")
    documents = load_documents(data_dir)
    
    if not documents:
        print("❌ No documents found! Please add documents to the data/raw_docs directory.")
        return
    
    print(f"\n✅ Loaded {len(documents)} documents")
    
    # Split documents into chunks
    print(f"\n✂️ Splitting documents (chunk_size={chunk_size}, overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    texts = text_splitter.split_documents(documents)
    print(f"✅ Created {len(texts)} text chunks")
    
    # Add chunk metadata
    for i, text in enumerate(texts):
        text.metadata["chunk"] = i
        text.metadata["file_name"] = os.path.basename(text.metadata.get("source", "unknown"))
    
    # Create embeddings
    print("\n🔢 Creating embeddings (this may take a while)...")
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create FAISS vector store
    print("🏗️ Building FAISS index...")
    vectorstore = FAISS.from_documents(texts, embedding_model)
    
    # Save to disk
    print(f"\n💾 Saving vector store to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    vectorstore.save_local(output_dir)
    
    print("\n" + "="*50)
    print("✅ Vector store built successfully!")
    print("="*50)
    print(f"\nLocation: {os.path.abspath(output_dir)}")
    print(f"Total chunks indexed: {len(texts)}")
    print("\nYou can now run your application with: python asgi_app.py")

if __name__ == "__main__":
    # Build the index
    build_vector_store(
        data_dir="data/raw_docs",
        output_dir="vector_store/faiss_index",
        chunk_size=1000,
        chunk_overlap=200
    )