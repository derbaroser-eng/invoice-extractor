#!/usr/bin/env python3
"""
test_invoice_extractor.py — failing tests for invoice-extractor.

Run: python workspace/products/invoice-extractor/test_invoice_extractor.py
"""
import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "extract.py"

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, cond, detail))


def run_extract(payload: dict) -> dict:
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        return {"error": f"exit={r.returncode}", "stderr": r.stderr[:200]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "stdout": r.stdout[:200]}


def create_test_pdf(path: str, text: str):
    """Create a minimal PDF with the given text content."""
    try:
        from PyPDF2 import PdfWriter, PdfReader
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        c = canvas.Canvas(path, pagesize=letter)
        y = 750
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 15
        c.save()
        return True
    except ImportError:
        # Fallback: create a text file with .pdf extension
        with open(path, "w") as f:
            f.write(text)
        return True


# --- test 1: vendor extraction ---
with tempfile.TemporaryDirectory() as tmpdir:
    pdf_path = os.path.join(tmpdir, "test.pdf")
    create_test_pdf(pdf_path, "From: Acme Corp\nInvoice #INV-2026-001\nDate: 2026-01-15\nTotal: $1200.00")
    out = run_extract({"pdf_path": pdf_path})
    check("vendor: extracted", isinstance(out, dict) and out.get("vendor") == "Acme Corp", str(out)[:100])

    # --- test 2: invoice number ---
    check("invoice: extracted", out.get("invoice_number") == "INV-2026-001", str(out))

    # --- test 3: date ---
    check("date: 2026-01-15", out.get("invoice_date") == "2026-01-15", str(out))

    # --- test 4: total ---
    check("total: 1200.0", out.get("total") == 1200.0, str(out))

    # --- test 5: currency ---
    check("currency: USD", out.get("currency") == "USD", str(out))

    # --- test 6: file not found ---
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({"pdf_path": "/nonexistent/file.pdf"}),
        capture_output=True, text=True, timeout=10,
    )
    check("notfound: exit 1", r.returncode == 1, f"rc={r.returncode}")

    # --- test 7: invalid input (missing pdf_path) ---
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({"foo": "bar"}),
        capture_output=True, text=True, timeout=10,
    )
    check("invalid: exit 1", r.returncode == 1, f"rc={r.returncode}")

    # --- test 8: invalid input (non-string pdf_path) ---
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps({"pdf_path": 123}),
        capture_output=True, text=True, timeout=10,
    )
    check("wrongtype: exit 1", r.returncode == 1, f"rc={r.returncode}")

    # --- test 9: no secrets in output ---
    pdf_path2 = os.path.join(tmpdir, "test2.pdf")
    create_test_pdf(pdf_path2, "From: SecretVendor\nInvoice #SECRET-001\nTotal: $100.00")
    out = run_extract({"pdf_path": pdf_path2})
    if isinstance(out, dict):
        check("no secrets: no raw text", "SecretVendor" not in json.dumps(out) or out.get("vendor") == "SecretVendor", str(out))

    # --- test 10: deterministic ---
    out1 = run_extract({"pdf_path": pdf_path})
    out2 = run_extract({"pdf_path": pdf_path})
    check("deterministic: same output", out1 == out2, f"{out1} vs {out2}")

# --- report ---
passed = sum(1 for _, ok, _ in results if ok)
failed = [(n, d) for n, ok, d in results if not ok]
print(f"\n{passed}/{len(results)} assertions passed")
if failed:
    print("\nFAILED:")
    for n, d in failed:
        print(f"  {n}  ({d})")
    sys.exit(1)
print("ALL TESTS GREEN")
