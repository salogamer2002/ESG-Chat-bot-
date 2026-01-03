import tiktoken

def chunk_text(text, max_tokens=512):
    enc = tiktoken.get_encoding("cl100k_base")
    words = text.split()
    chunks, current_chunk = [], []

    for word in words:
        current_chunk.append(word)
        if len(enc.encode(" ".join(current_chunk))) > max_tokens:
            chunks.append(" ".join(current_chunk[:-1]))
            current_chunk = [word]
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks
