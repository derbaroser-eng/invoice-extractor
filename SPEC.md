# SPEC — PDF Invoice Extractor

## What it does

Takes a PDF invoice file and extracts key fields into structured JSON:
- Vendor name
- Invoice number
- Invoice date
- Due date
- Subtotal
- Tax amount
- Total amount
- Currency
- VAT number
- Line items (description, quantity, unit price, amount)

Uses PyPDF2 for text extraction, deterministic regex for field parsing.

## What it does NOT do

- Does not connect to any external API
- Does not use an LLM
- Does not store invoice data
- Does not validate against accounting rules

## Input

```json
{
  "pdf_path": "/path/to/invoice.pdf"
}
```

## Output

```json
{
  "vendor": "Acme Corp",
  "invoice_number": "INV-2026-001",
  "invoice_date": "2026-01-15",
  "due_date": "2026-02-15",
  "subtotal": 1000.00,
  "tax_amount": 200.00,
  "total": 1200.00,
  "currency": "USD",
  "vat_number": "US123456789",
  "line_items": [
    {
      "description": "Consulting services",
      "quantity": 10,
      "unit_price": 100.00,
      "amount": 1000.00
    }
  ]
}
```

## Exit codes

- `0` — success, fields extracted
- `1` — invalid input (missing `pdf_path`, file not found, not a PDF)
- `2` — no fields found (unrecognized invoice format)
- `3` — PDF parsing error (corrupted or encrypted PDF)

## Rules (deterministic, no ML)

### Vendor extraction
- Look for `From: <vendor>` or `Vendor: <vendor>` or `Bill From: <vendor>`
- If not found, look for the first line that looks like a company name (contains "Inc", "LLC", "Corp", "Ltd", "GmbH")
- If not found, `vendor: null`

### Invoice number
- Look for `Invoice #<number>` or `Invoice No: <number>` or `Invoice Number: <number>`
- Capture the number (alphanumeric with dashes)
- If not found, `invoice_number: null`

### Date extraction
- Look for `Date: <date>` or `Invoice Date: <date>`
- Date format: YYYY-MM-DD or MM/DD/YYYY
- Convert to YYYY-MM-DD
- If not found, `invoice_date: null`

### Amount extraction
- Look for `Total: $<amount>` or `Amount Due: $<amount>` or `Balance Due: $<amount>`
- Capture the number as a float
- If not found, `total: null`

### Currency
- `$` or `USD` → `USD`
- `€` or `EUR` → `EUR`
- `£` or `GBP` → `GBP`
- If not found, `currency: null`

### VAT number
- Look for `VAT: <number>` or `VAT Number: <number>` or `Tax ID: <number>`
- Capture the number (alphanumeric)
- If not found, `vat_number: null`

### Line items
- Look for lines matching pattern: `<description> <quantity> x $<unit_price> = $<amount>`
- Or: `<description> <quantity> $<unit_price> $<amount>`
- If no line items found, `line_items: []`

## Constraints

- No external API calls
- No file I/O beyond reading the PDF and writing stdout
- No secrets in output
- Deterministic: same input → same output
