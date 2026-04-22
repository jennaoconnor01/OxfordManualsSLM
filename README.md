Oxford Etcher Manual RAG Chatbot
A Retrieval-Augmented Generation (RAG) system that allows engineers and technicians to query Oxford PlasmaLab semiconductor etching manuals through a natural language interface. Instead of manually searching through hundreds of pages of technical documentation, users can ask plain-English questions and receive accurate, grounded answers in seconds.

How It Works
The system is built as a full end-to-end pipeline:

PDF Extraction — Raw text is extracted from Oxford PlasmaLab PDF manuals using the Unstructured library, preserving layout metadata like page numbers and coordinates.

Cleaning — A custom cleaning pipeline removes headers, footers, table of contents lines, figure labels, page number blocks, duplicate content, and visual noise that commonly pollutes PDF extraction output.

Chunking — The cleaned text is sentence-tokenized using NLTK and chunked into semantically meaningful segments (max ~1200 characters) with a 2-sentence overlap to preserve context across chunk boundaries. This produces 646 RAG-ready chunks.

Embedding — Each chunk is embedded using OpenAI's text-embedding-3-large model in batches of 50, then stored in a FAISS vector index for fast similarity search.

Querying — At query time, the user's question is embedded and matched against the FAISS index to retrieve the top-k most relevant chunks. Those chunks are passed as context to a local Llama 3 model (via Ollama), which generates a concise, grounded answer.

Example
Enter a question: How do I recover from a red process abort alert?

Answer: Red alerts are typically caused by a process setpoint being out of
tolerance for too long. To recover: check the most recent process log to find
the remaining process time, construct a new process with a modified time, and
enable the 'Ignore tolerance' option if authorized. Monitor the machine closely
when operating in this condition.
Project Structure
.
├── extract_all_pdfs.py     # Step 1: Extract text from PDF manuals
├── clean_text.py           # Step 2: Clean and filter extracted text
├── chunk2.py               # Step 3: Sentence tokenize and chunk
├── embed.py                # Step 4: Embed chunks and build FAISS index
├── rag_engine.py           # Step 5: Query the chatbot
├── raggified_chunks.jsonl  # Pre-processed chunk data (646 chunks)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── .gitignore
Setup
Prerequisites
Python 3.11+
Ollama installed locally with the llama3 model pulled
An OpenAI API key
Installation
Clone the repository:
git clone https://github.com/your-username/oxford-rag-chatbot.git
cd oxford-rag-chatbot
Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
Set up your environment variables:
cp .env.example .env
Then open .env and add your OpenAI API key:

OPENAI_API_KEY=your-openai-api-key-here
Pull the Llama 3 model via Ollama:
ollama pull llama3
Usage
Option A: Use the pre-built chunks (recommended)
The repository includes raggified_chunks.jsonl with 646 pre-processed chunks ready to embed. Skip straight to building the index:

python embed.py
This will generate the oxford_faiss_index/ folder locally.

Option B: Run the full pipeline from raw PDFs
If you have your own Oxford manual PDFs:

Place PDF files in a data/ folder
Run each step in order:
python extract_all_pdfs.py
python clean_text.py
python chunk2.py
python embed.py
Start the chatbot
python rag_engine.py
Tech Stack
Python — core language
Unstructured — PDF text extraction
NLTK — sentence tokenization
OpenAI API — text embeddings (text-embedding-3-large)
FAISS — vector similarity search
LangChain — orchestration layer
Ollama + Llama 3 — local language model for answer generation
python-dotenv — environment variable management
Notes
The FAISS index files are not committed to this repository. Run embed.py to generate them locally.
The system is designed to answer only from retrieved context. If the answer is not found in the documentation, the model will say so rather than hallucinate.
Raw PDF files and intermediate extraction outputs are excluded from the repository via .gitignore.
License
MIT
