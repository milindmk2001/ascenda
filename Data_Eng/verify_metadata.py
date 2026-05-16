import json
from pathlib import Path

PDF_DIR       = Path(r"C:\projects\Data_Engineering\sourceData\openumn\Phy")
METADATA_JSON = Path(r"C:\projects\Data_Engineering\book_metadata.json")

EXPECTED_COUNT = 10

def check():
    # ── Load PDFs on disk ─────────────────────────────────────
    pdf_files  = sorted(PDF_DIR.glob("**/*.pdf"))
    pdf_names  = {f.name for f in pdf_files}

    print(f"\n{'='*70}")
    print(f"  METADATA VERIFICATION REPORT")
    print(f"{'='*70}")
    print(f"  PDFs found on disk : {len(pdf_files)}")

    # ── Load JSON ─────────────────────────────────────────────
    if not METADATA_JSON.exists():
        print(f"\n  ❌ book_metadata.json NOT FOUND at:\n     {METADATA_JSON}")
        print(f"     Run scan_metadata.py first.\n")
        return

    with open(METADATA_JSON, encoding="utf-8") as f:
        metadata = json.load(f)

    json_names = set(metadata.keys())
    matched    = pdf_names & json_names
    missing    = pdf_names - json_names    # PDFs not in JSON
    orphaned   = json_names - pdf_names   # JSON entries with no PDF on disk

    print(f"  Entries in JSON    : {len(metadata)}")
    print(f"  Matched            : {len(matched)}/{EXPECTED_COUNT}")
    print(f"  Missing from JSON  : {len(missing)}")
    print(f"  Orphaned in JSON   : {len(orphaned)}")
    print(f"{'='*70}\n")

    # ── Per-book field detail ─────────────────────────────────
    print(f"  {'#':<3} {'Filename':<50} {'Title':<6} {'Authors':<8} {'URL':<5} {'Type':<10}")
    print(f"  {'-'*85}")

    warnings = []
    for i, name in enumerate(sorted(matched), 1):
        m = metadata[name]

        title_ok   = "✅" if m.get("title")                    else "❌"
        authors_ok = "✅" if m.get("authors")                  else "⚠️ "
        url_ok     = "✅" if m.get("source_url","").startswith("http") else "⚠️ "
        type_ok    = "✅" if m.get("curriculum_type")          else "❌"

        # Truncate long filenames for display
        display_name = name if len(name) <= 48 else name[:45] + "..."
        print(f"  {i:<3} {display_name:<50} {title_ok:<6} {authors_ok:<8} {url_ok:<5} {type_ok}")

        if not m.get("authors"):
            warnings.append(f"  ⚠️  No authors detected   → {name}")
        if not m.get("source_url","").startswith("http"):
            warnings.append(f"  ⚠️  source_url blank       → {name}")
        if m.get("license","") not in ["CC-BY-4.0","CC-BY-3.0","CC-BY-SA-4.0","CC-BY-SA-3.0"]:
            warnings.append(f"  ⚠️  Verify license value   → {name}  [{m.get('license')}]")

    # ── Missing PDFs ──────────────────────────────────────────
    if missing:
        print(f"\n  ❌ PDFs NOT in JSON — re-run scan_metadata.py:")
        for name in sorted(missing):
            print(f"     • {name}")

    # ── Orphaned entries ──────────────────────────────────────
    if orphaned:
        print(f"\n  ⚠️  JSON entries with no matching PDF on disk:")
        for name in sorted(orphaned):
            print(f"     • {name}")

    # ── Warnings ──────────────────────────────────────────────
    if warnings:
        print(f"\n  WARNINGS — fix in book_metadata.json before chunking:")
        for w in warnings:
            print(w)

    # ── Full metadata printout ────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  FULL METADATA PREVIEW")
    print(f"{'='*70}")
    for name in sorted(matched):
        m = metadata[name]
        print(f"\n  📄 {name}")
        print(f"     Title      : {m.get('title','?')}")
        print(f"     Authors    : {m.get('authors','?')}")
        print(f"     Subject    : {m.get('subject','?')}")
        print(f"     Edition    : {m.get('edition','?')}")
        print(f"     Publisher  : {m.get('publisher','?')}")
        print(f"     Year       : {m.get('pub_year','?')}")
        print(f"     License    : {m.get('license','?')}")
        print(f"     Type       : {m.get('curriculum_type','?')}")
        print(f"     Solutions? : {m.get('is_solutions', False)}")
        print(f"     Source URL : {m.get('source_url','[BLANK]')}")
        print(f"     Attribution: {m.get('attribution','?')}")

    # ── Final verdict ─────────────────────────────────────────
    print(f"\n{'='*70}")
    if len(matched) == EXPECTED_COUNT and not missing:
        if not warnings:
            print(f"  ✅ ALL {EXPECTED_COUNT} PDFs captured and verified — ready to run chunker.py")
        else:
            print(f"  ⚠️  All {EXPECTED_COUNT} PDFs captured but {len(warnings)} warning(s) above")
            print(f"     Fix warnings in book_metadata.json then run chunker.py")
    else:
        print(f"  ❌ Only {len(matched)}/{EXPECTED_COUNT} PDFs captured")
        print(f"     Re-run scan_metadata.py to fix missing entries")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    check()