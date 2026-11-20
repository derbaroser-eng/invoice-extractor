#!/usr/bin/env python3
"""
extract.py — deterministic PDF invoice field extractor.

Reads JSON from stdin, writes JSON to stdout.
No external calls, no file I/O beyond reading the PDF, no secrets in output.
"""
import json
import re
import sys
import os


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyPDF2, fallback to plain text."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception:
        # Fallback: try reading as plain text
        try:
            with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return None


def extract_vendor(text):
    m = re.search(r"(?:From|Vendor|Bill From):\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    for line in text.split("\n"):
        if any(k in line for k in ["Inc", "LLC", "Corp", "Ltd", "GmbH"]):
            return line.strip()
    return None


def extract_invoice_number(text):
    m = re.search(r"Invoice\s*#\s*([\w-]+)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"Invoice\s*(?:No|Number):\s*([\w-]+)", text, re.IGNORECASE)
    return m.group(1) if m else None


def extract_date(text):
    m = re.search(r"(?:Date|Invoice Date):\s*(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"(?:Date|Invoice Date):\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if m:
        parts = m.group(1).split("/")
        return f"{parts[2]}-{parts[0]}-{parts[1]}"
    return None


def extract_total(text):
    m = re.search(r"(?:Total|Amount Due|Balance Due):\s*\$\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def extract_currency(text):
    if re.search(r"\$|USD", text, re.IGNORECASE):
        return "USD"
    if re.search(r"€|EUR", text, re.IGNORECASE):
        return "EUR"
    if re.search(r"£|GBP", text, re.IGNORECASE):
        return "GBP"
    return None


def extract_vat(text):
    m = re.search(r"(?:VAT|VAT Number|Tax ID):\s*([\w-]+)", text, re.IGNORECASE)
    return m.group(1) if m else None


def extract_fields(text):
    return {
        "vendor": extract_vendor(text),
        "invoice_number": extract_invoice_number(text),
        "invoice_date": extract_date(text),
        "total": extract_total(text),
        "currency": extract_currency(text),
        "vat_number": extract_vat(text),
        "line_items": []
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("error: invalid JSON", file=sys.stderr)
        return 1

    if not isinstance(data, dict) or "pdf_path" not in data:
        print("error: missing 'pdf_path' field", file=sys.stderr)
        return 1

    if not isinstance(data["pdf_path"], str):
        print("error: 'pdf_path' must be a string", file=sys.stderr)
        return 1

    if not os.path.exists(data["pdf_path"]):
        print(f"error: file not found: {data['pdf_path']}", file=sys.stderr)
        return 1

    text = extract_text_from_pdf(data["pdf_path"])
    if text is None:
        print("error: could not extract text from PDF", file=sys.stderr)
        return 3

    result = extract_fields(text)

    if all(v is None for v in result.values()):
        print("error: no fields found in invoice", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
