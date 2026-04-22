import nltk
nltk.download("punkt")
import json
from nltk.tokenize import sent_tokenize
import os
import re

INPUT_FILE = r"C:\Users\jenna\Downloads\slm_mvp\clean_extracted\cleaned_chunks.jsonl"
OUTPUT_FILE = r"C:\Users\jenna\Downloads\clean_extracted\raggified_chunks.jsonl"

# -------------------------------
# CLEANERS
# -------------------------------

LIST_NUMBERS_PATTERN = re.compile(
    r"(?:\b\d+\s*){5,}"  # sequences of 5+ numbers in a row
)

def remove_number_spam(text):
    """Remove long list-number sequences like '1 2 3 4 5 6 7 8...'"""
    cleaned = LIST_NUMBERS_PATTERN.sub("", text)
    return " ".join(cleaned.split())  # normalize spacing

# -------------------------------
# LOAD CLEANED INPUT
# -------------------------------

def load_cleaned_file(path):
    texts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "text" in obj and obj["text"].strip():
                    cleaned = obj["text"].strip()
                    cleaned = remove_number_spam(cleaned)
                    texts.append(cleaned)
            except json.JSONDecodeError:
                continue
    return texts

# -------------------------------
# SENTENCE TOKENIZATION
# -------------------------------

def split_into_sentences(text_list):
    sentences = []
    for block in text_list:
        sents = sent_tokenize(block)
        for s in sents:
            # Remove extremely short noise
            if len(s.strip()) > 2:
                sentences.append(s.strip())
    return sentences

# -------------------------------
# CHUNKING FUNCTION
# -------------------------------

def chunk_by_sentences(sentences, max_tokens=1200, overlap_sentences=2):
    chunks = []
    current_chunk = []
    current_length = 0

    for sent in sentences:
        sent_len = len(sent)

        if current_length + sent_len > max_tokens:
            chunks.append(" ".join(current_chunk).strip())
            current_chunk = current_chunk[-overlap_sentences:]
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(sent)
        current_length += sent_len

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    return chunks

# -------------------------------
# WRITE FINAL RAG-READY JSON
# -------------------------------

def write_rag_json(chunks):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            obj = {
                "id": i,
                "source": "cleaned_manuals",
                "chunk": chunk,
                "num_sentences": len(sent_tokenize(chunk)),
                "length": len(chunk)
            }
            json.dump(obj, f)
            f.write("\n")

    print(f"RAG-ready file written → {OUTPUT_FILE}")
    print(f"Total chunks: {len(chunks)}")

# -------------------------------
# MAIN
# -------------------------------

clean_blocks = load_cleaned_file(INPUT_FILE)
sentences = split_into_sentences(clean_blocks)
chunks = chunk_by_sentences(sentences)

write_rag_json(chunks)
