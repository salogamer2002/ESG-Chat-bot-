import asyncio
import re
from typing import List

import fitz  # PyMuPDF for PDF handling
import tiktoken
from docx import Document as DocxDocument  # for DOCX support
import os

from langchain.text_splitter import TokenTextSplitter
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI

def clean_output(report_text: str) -> str:
    # Remove 'Standards Referenced' section if it says 'No specific standards referenced.'
    pattern = r"\*\*Standards Referenced:\*\*\s*[-–•]\s*No specific standards referenced\.?\s*"
    return re.sub(pattern, "", report_text, flags=re.IGNORECASE)

def extract_confidence(text):
    match = re.search(r"Confidence Level:\s*(High|Medium|Low)", text, re.IGNORECASE)
    return match.group(1) if match else "Unknown"

def extract_page_number(text):
    match = re.search(r"\[Page (\d+)\]", text)
    return int(match.group(1)) if match else float("inf")  # or 0 if you want such entries first

semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent API calls

# Tunables
CHUNK_SIZE = 1024
OVERLAP = 50
MAX_TOKENS = 12000  # limit for GPT-3.5-turbo context

def extract_text_by_page(filepath: str):
    _, ext = os.path.splitext(filepath.lower())
    if ext == ".pdf":
        doc = fitz.open(filepath)
        return [(i + 1, page.get_text()) for i, page in enumerate(doc)]
    elif ext == ".docx":
        doc = DocxDocument(filepath)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        
        # Simulate "pages" in docx by splitting every N lines
        simulated_pages = []
        lines_per_page = 30  # You can adjust this to better simulate page breaks
        for i in range(0, len(full_text), lines_per_page):
            page_text = "\n".join(full_text[i:i + lines_per_page])
            simulated_pages.append((i // lines_per_page + 1, page_text))

        return simulated_pages

    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

def chunk_document(text: str, chunk_size=CHUNK_SIZE, overlap=OVERLAP) -> List[str]:
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return splitter.split_text(text)

def batch_texts(texts: List[str], max_tokens: int, tokenizer) -> List[List[str]]:
    batches, current_batch, current_tokens = [], [], 0
    for text in texts:
        tokens = len(tokenizer.encode(text))
        if current_tokens + tokens > max_tokens:
            batches.append(current_batch)
            current_batch, current_tokens = [], 0
        current_batch.append(text)
        current_tokens += tokens
    if current_batch:
        batches.append(current_batch)
    return batches

def chunk_with_page_tracking(pages, chunk_size=1024, overlap=50):
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    page_chunks = [{"page": page_num, "text": text} for page_num, text in pages]

    full_text = "\n\n".join([p["text"] for p in page_chunks])
    chunks = splitter.split_text(full_text)

    chunk_metadata = []
    for chunk in chunks:
        matched_page = None
        for page_data in page_chunks:
            if chunk[:20] in page_data["text"]:
                matched_page = page_data["page"]
                break

        chunk_metadata.append({
            "chunk": chunk,
            "page": matched_page if matched_page is not None else "?",
            "section_title": f"Section for Page {matched_page if matched_page is not None else '?'}"
        })

    return chunk_metadata

async def run_gap(chunk: str, i: int, gap_chain, semaphore, page, section_title=None):
    async with semaphore:
        query = f"""
This is a section from a company policy or ESG report:

📄 Page {page} — {section_title or "Untitled Section"}

---
{chunk}
---

Please evaluate this content for ESG compliance:

✅ Strengths:
- Identify specific ESG best practices or frameworks followed.
- Mention any clear alignment with industry standards (e.g., GRI, TCFD, SASB).

🚩 Gaps:
- Highlight missing disclosures, vague language, or absent metrics.
- Identify inconsistencies or areas lacking transparency.

🛠️ Recommendations:
- Provide actionable, evidence-based improvements.
- Suggest how the company can close each identified gap.

📚 **Standards Referenced:**  
- List any ESG standards, frameworks, or regulations cited or clearly implied (e.g., GRI, SASB, TCFD, UN SDGs, CDP, ISO 26000).  
- If none are mentioned, state: "No specific standards referenced."

📝 Supporting Quote:
- Include one short quote from the section that supports a key finding. Wrap it in quotes.

📊 Confidence Level:
- Conclude with: Confidence Level: High / Medium / Low
- This reflects how well-supported your analysis is based on content clarity and completeness and supports your conclusions and the presence of sufficient detail.

Return a professional and structured assessment in full sentences.
"""

        loop = asyncio.get_event_loop()
        for attempt in range(1):  # try 3 times
            try:
                result = await loop.run_in_executor(None, gap_chain.invoke, query)
                return i, result, page, section_title
            except Exception as e:
                if "429" in str(e) or "Rate limit" in str(e):
                    wait_time = 2 ** attempt
                    print(f"Rate limit hit. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise  # unexpected error

async def analyze_document_for_compliance(filepath: str, gap_chain) -> str:
    text = extract_text_by_page(filepath)
    chunks = chunk_with_page_tracking(text)

    # Step 1: Parallel chunk evaluation
    tasks = [
        run_gap(chunk_data["chunk"], i, gap_chain, semaphore, chunk_data["page"], chunk_data["section_title"])
        for i, chunk_data in enumerate(chunks)
    ]
    results = await asyncio.gather(*tasks)

    chunk_analyses = []
    for i, response, page, section_title in results:
        answer = response["result"]
        sources = response.get("source_documents", [])
        if sources and len(sources) >= 1:
            chunk_analyses.append(
                f"[Page {page}] {section_title or ''}:\n{answer.strip()}\n(Supporting context from Page {page}, {section_title})"
            )

    chunk_analyses.sort(key=extract_page_number)

    print("------------------------------------------------------------------------")
    print("chunk_analyses")
    print("------------------------------------------------------------------------")
    print(chunk_analyses)
    print("------------------------------------------------------------------------")
    print("------------------------------------------------------------------------")

    # Step 2: Intermediate summaries
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

    batch_prompt = PromptTemplate.from_template("""
You are an ESG compliance auditor.

You will receive multiple section-wise evaluations with page numbers and section titles.

Retain the references (e.g., [Page 12, Governance Overview]) in your summary.

Do not invent or generalize page numbers.

{input}
""")
    summarizer = batch_prompt | llm

    batches = batch_texts(chunk_analyses, MAX_TOKENS, tokenizer)
    intermediate_summaries = []
    for batch in batches:
        text = "\n\n".join(batch)
        summary = await asyncio.get_event_loop().run_in_executor(None, summarizer.invoke, {"input": text})
        intermediate_summaries.append(summary.content.strip())

    # Step 3: Final summary
    final_summary_prompt = PromptTemplate.from_template("""
You are an ESG compliance auditor.

You are provided with evaluations for various sections of a corporate ESG document.
Each section includes a page number and a section title in this format: `[Page X] Section Title`.

Your task is to write a **comprehensive compliance report** with the following structure:

---

**Strengths:**
- Summarize strengths across all sections, referencing specific pages and section titles where applicable. Example: (Page 5, Executive Summary)

**Compliance Gaps:**
- For each gap, include the precise reference from the original input (e.g., Page 12, Risk Management Section).
- Do not group gaps under "Various" — preserve their source location.
- Avoid repeating the same issue without a unique reference.

**Recommendations:**
- Match each recommendation to a corresponding gap, and reference the same page/section title as noted.
- Ensure recommendations are specific and evidence-based.

**Standards Referenced:**  
- List any ESG standards, frameworks, or regulations cited or clearly implied (e.g., GRI, SASB, TCFD, UN SDGs, CDP, ISO 26000).  
- If none are mentioned, state: "No specific standards referenced."

**Supporting Quote(s):**
- Include up to 3 direct quotes from the evaluations, with exact reference (page/section) and wrap each in double quotes.

**Overall Confidence Level:**
High / Medium / Low — reason for this confidence level
                                                        
---

⚠️ Do NOT fabricate page numbers or section titles.
⚠️ Do NOT replace real references with "Various" or vague terms.
⚠️ Only report sections with findings. If no findings, skip it.

Evaluations:
{input}
""")



    final_summarizer = final_summary_prompt | llm
    final_input = "\n\n".join(intermediate_summaries)
    final_report = await asyncio.get_event_loop().run_in_executor(None, final_summarizer.invoke, {"input": final_input})

    final_report_cleaned = clean_output(final_report.content.strip())

    return final_report_cleaned
