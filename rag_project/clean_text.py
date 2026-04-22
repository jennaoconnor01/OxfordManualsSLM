import os
import json
import re
from collections import defaultdict

INPUT_DIR = r"C:\Users\jenna\Downloads\slm_mvp\extracted"       
OUTPUT_FILE = "cleaned_chunks.jsonl"

MAX_CHARS = 1200
MIN_CHARS = 200

def read_file(file):
    #reads file of JSON objects into a list type
    all_blocks = []

    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            text = obj["text"].strip()
            page = obj["metadata"]["page_number"]
            points = obj["metadata"]["coordinates"]["points"]
            height = obj["metadata"]["coordinates"]["layout_height"]

            y_top = points[0][1]
            norm_y = y_top / height

            block = {
                "text": text,
                "page": page,
                "norm_y": norm_y,
                "points": points,
                "height": height
            }

            all_blocks.append(block)
    return all_blocks

def normalize_for_repetition(text: str) -> str:
    # lower, collapse spaces, and blank out page numbers
    import re
    t = text.lower().strip()
    # replace sequences of digits with <NUM>
    t = re.sub(r'\d+', '<NUM>', t)
    # squeeze multiple spaces
    t = re.sub(r'\s+', ' ', t)
    return t

def detect_headers_footers(lines, min_pages=3, top_thresh=0.15, bot_thresh=0.9):
    """
    lines: list of dicts with keys: text, page, norm_y
    returns: set of ids or indices that are header/footer lines
    """
    from collections import defaultdict
    
    # 1) group by normalized text separately for top and bottom bands
    top_counts = defaultdict(set)   # norm_text -> set(pages)
    bot_counts = defaultdict(set)
    
    for i, line in enumerate(lines):
        tnorm = normalize_for_repetition(line["text"])
        y = line["norm_y"]
        p = line["page"]
        if y < top_thresh:
            top_counts[tnorm].add(p)
        elif y > bot_thresh:
            bot_counts[tnorm].add(p)
    
    # 2) find candidate header/footer patterns
    header_patterns = {
        t for t, pages in top_counts.items() if len(pages) >= min_pages
    }
    footer_patterns = {
        t for t, pages in bot_counts.items() if len(pages) >= min_pages
    }
    
    header_ids = set()
    footer_ids = set()
    
    # 3) mark individual lines
    for i, line in enumerate(lines):
        tnorm = normalize_for_repetition(line["text"])
        y = line["norm_y"]
        if y < top_thresh and tnorm in header_patterns:
            header_ids.add(i)
        elif y > bot_thresh and tnorm in footer_patterns:
            footer_ids.add(i)
    
    return header_ids, footer_ids

def remove_all_headers(file):
    blocks = read_file(file)
    headers, footers = detect_headers_footers(blocks)
    clean_blocks = [
    blk for i, blk in enumerate(blocks)
    if i not in headers and i not in footers
    ]
    return clean_blocks

def write_clean_blocks(cleaned_blocks, original_filename):
    OUTPUT_DIR = "clean_extracted"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    out_file = os.path.join(OUTPUT_DIR, "cleaned_chunks.jsonl")

    with open(out_file, "a", encoding="utf-8") as f:
        for block in cleaned_blocks:
            json.dump(block, f)
            f.write("\n")

    print("Saved cleaned output to:", out_file)

def remove_page_number_blocks(blocks):
    cleaned = []

    # Regexes for common page-number formats
    page_patterns = [
        r"^page\s*\d+$",                # Page 7
        r"^page\s+\w+$",                # Page ii
        r"^page\s+\w+\s+of\s+\w+$",     # Page ii of vi
        r"^\d+$",                       # 7
        r"^[ivxlcdm]+$",                # roman numerals (lowercase)
        r"^[IVXLCDM]+$",                # roman numerals (uppercase)
        r"^\d+\s*-\s*\d+$",             # 3-1, 12-1
        r"^\w+\s*-\s*\d+$"              # weird OCR like "iii-1"
    ]

    compiled = [re.compile(p, re.IGNORECASE) for p in page_patterns]

    for b in blocks:
        t = b["text"].strip()

        # Skip empty blocks
        if t == "":
            continue

        # If *entire text matches* a page-number pattern -> remove block
        if any(p.match(t) for p in compiled):
            continue

        cleaned.append(b)

    return cleaned

def normalize_whitespace(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def remove_duplicates(blocks):
    seen = set()
    unique = []
    for b in blocks:
        t = b["text"].strip()
        if t not in seen:
            seen.add(t)
            unique.append(b)
    return unique

def drop_short_blocks(blocks, min_len=15):
    return [b for b in blocks if len(b["text"].strip()) >= min_len]

def final_clean(blocks):
    cleaned = []
    for b in blocks:
        t = b["text"].strip()

        # Clean parentheses early
        t = clean_parenthetical(t).strip()

        # Skip unwanted blocks
        if not should_keep(t):
            continue

        # Normalize whitespace
        t = re.sub(r"\s+", " ", t).strip()

        b["text"] = t
        cleaned.append(b)

    return cleaned
def should_keep(text):
    t = text.strip()

    # Drop empty
    if not t:
        return False
    # TOC
    if is_toc_line(t):
        return False
    # Figure captions
    if is_figure_label(t):
        return False
    # Part table rows
    if is_part_table_row(t):
        return False
    # Visual garbage
    if is_visual_noise(t):
        return False

    return True
def is_visual_noise(text):
    # Repeating symbols
    if re.search(r"[-~=]{4,}", text):
        return True
    # Strings with almost no vowels → noise
    if len(re.findall(r"[aeiouAEIOU]", text)) < 2:
        if len(text) < 40:
            return True
    return False
def clean_parenthetical(text):
    return re.sub(r"\([^)]*\)", "", text)
def is_part_table_row(text):
    # 40%+ uppercase → part list, NOT real text
    letters = [c for c in text if c.isalpha()]
    if letters:
        cap_ratio = sum(c.isupper() for c in letters) / len(letters)
        if cap_ratio > 0.4:
            return True
    
    # Remove circuit/valve lines
    if re.search(r"\bG\s*[A-Z]+\b", text):
        return True
    if "valve" in text.lower() or "circuit" in text.lower():
        return True
    return False
def is_figure_label(text):
    if re.match(r"^Item\s*\(\d+\)$", text, re.IGNORECASE):
        return True
    if re.match(r"^\(\d+\)", text):  # (1), (2), (3)
        return True
    if "VIEW" in text.upper():
        return True
    if re.match(r"^\w+ Module$", text):
        return True
    return False
def is_toc_line(text):
    # Remove any short "Section title" style entries
    if len(text.split()) <= 6:
        return True
    # Remove lines that look like category titles
    if re.match(r"^[A-Z][a-z]+(\s+[a-zA-Z]+){0,5}$", text):
        return True
    return False

first_file = os.path.join(INPUT_DIR, os.listdir(INPUT_DIR)[2])

blocks = remove_all_headers(first_file)
blocks = remove_page_number_blocks(blocks)
blocks = drop_short_blocks(blocks)
blocks = final_clean(blocks)
blocks = remove_duplicates(blocks)

write_clean_blocks(blocks, first_file)

print("Final count:", len(blocks))





