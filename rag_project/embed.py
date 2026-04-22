import json
import time
import os
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ----------------------------------------------
# 1. LOAD CHUNKS
# ----------------------------------------------
client = OpenAI()  # Uses OPENAI_API_KEY from environment

file_path = "raggified_chunks.jsonl"

chunks = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

texts = [c["chunk"] for c in chunks]
print("Loaded", len(texts), "chunks")

# ----------------------------------------------
# 2. EMBEDDING BATCHES
# ----------------------------------------------
def embed_batch(batch):
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print("Error:", e)
        print("Retrying in 5 seconds...")
        time.sleep(5)
        return embed_batch(batch)

batch_size = 50
all_embeddings = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    print(f"Embedding batch {i//batch_size + 1} of {len(texts)//batch_size + 1}...")
    batch_embeddings = embed_batch(batch)
    all_embeddings.extend(batch_embeddings)

print("Total embeddings:", len(all_embeddings))
print("Vector dimension:", len(all_embeddings[0]))

# ----------------------------------------------
# 3. BUILD METADATA LIST
# ----------------------------------------------
metadatas = []
for c in chunks:
    metadatas.append({
        "id": c["id"],
        "source": c["source"],
        "num_sentences": c.get("num_sentences"),
        "length": c.get("length"),
    })

# ----------------------------------------------
# 4. BUILD PAIRS = (text, embedding)
# ----------------------------------------------
pairs = []
for i, c in enumerate(chunks):
    pairs.append((c["chunk"], all_embeddings[i]))

# ----------------------------------------------
# 5. CREATE FAISS INDEX
# ----------------------------------------------
embedding_fn = OpenAIEmbeddings(model="text-embedding-3-large")

vectorstore = FAISS.from_embeddings(
    pairs,
    embedding_fn,
    metadatas
)

# ----------------------------------------------
# 6. SAVE THE INDEX
# ----------------------------------------------
vectorstore.save_local("oxford_faiss_index")
print("FAISS index saved successfully!")
