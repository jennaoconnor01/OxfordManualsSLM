import os
from openai import OpenAI
import ollama
from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize embedding function using key from environment
embedding_fn = OpenAIEmbeddings(model="text-embedding-3-large")

# Load FAISS index
vs = FAISS.load_local(
    "oxford_faiss_index",
    embeddings=embedding_fn,
    allow_dangerous_deserialization=True
)

def retrieve_chunks(question: str, k: int = 4) -> List[str]:
    docs = vs.similarity_search(question, k=k)
    return [d.page_content for d in docs]

client = OpenAI()

def build_prompt(question: str, chunks: List[str]) -> str:
    context = "\n\n".join(chunks)
    return f"""
You are a field service engineering assistant for semiconductor etchers.

Use ONLY the information below to answer.
If the answer is not found, respond:
"I do not have this information in the knowledge base."

CONTEXT:
{context}

QUESTION:
{question}

Provide a concise field-service-style answer.
"""

def generate_answer(prompt: str) -> str:
    response = ollama.generate(
        model="llama3",
        prompt=prompt
    )
    return response["response"]

def rag_query(question: str):
    chunks = retrieve_chunks(question)
    prompt = build_prompt(question, chunks)
    return generate_answer(prompt)


if __name__ == "__main__":
    print("Field Service Assistant Ready. Type 'exit' to quit.\n")

    while True:
        question = input("Enter a question: ")

        if question.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        answer = rag_query(question)
        print("Answer:", answer, "\n")
