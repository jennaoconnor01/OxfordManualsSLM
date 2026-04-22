import os
import json
from unstructured.partition.pdf import partition_pdf

# Paths
DATA_DIR = "data"
OUTPUT_DIR = "extracted"

def extract_pdf(pdf_path, output_path):
    print(f"Extracting: {pdf_path}")
  
    elements = partition_pdf(
    filename=pdf_path,
    strategy="fast",
    infer_table_structure=True,
    include_page_breaks=False,
    extract_image_block_types=[],
    extract_attachment_block_types=[]
)   


    # Convert each element to a dict
    rows = []
    for e in elements:
        rows.append({
            "type": e.category,
            "text": e.text,
            "metadata": e.metadata.to_dict() if e.metadata else {}
        })

    # Save as JSONL file
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f" Saved {len(rows)} elements to: {output_path}")

def main():
    for filename in os.listdir(DATA_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(DATA_DIR, filename)
            output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".jsonl"))

            extract_pdf(pdf_path, output_path)

if __name__ == "__main__":
    main()
