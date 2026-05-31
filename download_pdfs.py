import os
import sys
import httpx
import fitz

OUT_DIR = "data/sample_docs"
TARGET = os.path.join(OUT_DIR, "who_hiv_guidelines_2023.pdf")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}

ATTEMPTS = [
    (
        "https://iris.who.int/bitstream/handle/10665/376625/9789240085138-eng.pdf",
        "Attempt A",
        None,
    ),
    (
        "https://iris.who.int/bitstream/handle/10665/368163/9789240075061-eng.pdf",
        "Attempt B",
        None,
    ),
    (
        "https://iris.who.int/bitstream/handle/10665/342669/9789240031593-eng.pdf",
        "Attempt C",
        None,
    ),
    (
        "https://iris.who.int/bitstream/handle/10665/360883/9789240054981-eng.pdf",
        "Fallback",
        None,
    ),
]

# Step 1 — delete existing file
if os.path.exists(TARGET):
    os.remove(TARGET)
    print(f"Deleted {TARGET}")

os.makedirs(OUT_DIR, exist_ok=True)

def try_download(url: str, label: str, min_size_kb: int = 500, min_pages: int = 30) -> tuple[bool, str, dict]:
    print(f"\n{label}: {url}")
    tmp = TARGET + ".tmp"
    try:
        with httpx.Client(follow_redirects=True, timeout=120, headers=HEADERS) as client:
            r = client.get(url)
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}", {}
            with open(tmp, "wb") as f:
                f.write(r.content)
    except Exception as e:
        return False, f"download error: {e}", {}

    size_kb = os.path.getsize(tmp) / 1024
    if size_kb < min_size_kb:
        os.remove(tmp)
        return False, f"size {size_kb:.1f} KB < {min_size_kb} KB", {}

    try:
        doc = fitz.open(tmp)
        pages = doc.page_count
        page1_text = doc[0].get_text()
        doc.close()
    except Exception as e:
        os.remove(tmp)
        return False, f"fitz.open() failed: {e}", {}

    if pages < min_pages:
        os.remove(tmp)
        return False, f"only {pages} pages < {min_pages}", {}

    if "hiv" not in page1_text.lower() and "guideline" not in page1_text.lower():
        os.remove(tmp)
        return False, "page 1 text contains neither 'HIV' nor 'guideline'", {}

    os.rename(tmp, TARGET)
    return True, "", {"size_kb": size_kb, "pages": pages, "page1_text": page1_text}

chosen_label = None
chosen_meta = {}

for url, label, _ in ATTEMPTS[:-1]:  # try A, B, C first
    ok, reason, meta = try_download(url, label)
    if ok:
        print(f"  PASS: {label}")
        chosen_label = label
        chosen_meta = meta
        break
    else:
        print(f"  FAIL: {reason}")

if chosen_label is None:
    url, label, _ = ATTEMPTS[-1]  # fallback
    print(f"\nAll primary attempts failed — trying {label}")
    ok, reason, meta = try_download(url, label, min_size_kb=100, min_pages=10)
    if ok:
        print(f"  PASS: {label} (fallback)")
        chosen_label = label
        chosen_meta = meta
    else:
        print(f"  FAIL fallback: {reason}")
        print("\nCould not download any suitable 2023 PDF.")
        sys.exit(1)

# Step 4 — print final result
size_kb = chosen_meta["size_kb"]
pages = chosen_meta["pages"]
text_snippet = chosen_meta["page1_text"][:200].replace("\n", " ")

print(f"\n--- Final result ---")
print(f"  file:  {TARGET}")
print(f"  size:  {size_kb:.1f} KB")
print(f"  pages: {pages}")
print(f"  page1: {text_snippet!r}")

# Step 5 — detect year from page 1 text and update seed_data.py
import re

year_match = re.search(r'\b(20\d{2})\b', chosen_meta["page1_text"])
pub_year = int(year_match.group(1)) if year_match else 2023

# pick a plausible month: 1 = safe default
pub_date = f"datetime({pub_year}, 1, 1)"

seed_path = "seed_data.py"
with open(seed_path) as f:
    src = f.read()

# Replace the 2023 entry's published_date line
old = '        "published_date": datetime(2023, 7, 1),'
new = f'        "published_date": {pub_date},'
if old in src:
    src = src.replace(old, new)
    with open(seed_path, "w") as f:
        f.write(src)
    print(f"\nUpdated seed_data.py: published_date → {pub_date}")
else:
    print(f"\nWARN: could not find 2023 published_date line in seed_data.py — update manually")

# Print the updated DEMO_DOCS entry
print("\nUpdated DEMO_DOCS entry for 2023 doc:")
print(f'''    {{
        "path": "data/sample_docs/who_hiv_guidelines_2023.pdf",
        "source_id": "who_hiv_guidelines_2023",
        "published_date": {pub_date},
        "domain": Domain.MEDICAL,
        "source_url": "{url}",
        "source_authority": 0.95,
    }},''')
