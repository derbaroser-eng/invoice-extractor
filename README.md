# Invoice Extractor

Extract fields from PDF invoices without OCR or LLM.

## Try it

- **Live demo:** https://derbaroser-eng.github.io/invoice-extractor/
- **Free tier:** download and use locally
- **Name your price:** from EUR1
- **Full price:** See pricing on the live page

## Why deterministic?

An LLM doing this is a black box you cannot audit. When a tool says "this is an approval", you need to know why. A rule you can read is a rule you can trust, debug, and improve.

## Part of the AURUM B2B Suite

This is one of 10 deterministic B2B tools for SaaS teams built by [derbaroser-eng](https://github.com/derbaroser-eng).

See all tools: https://derbaroser-eng.github.io/products/

Built with Python. Standard library only. No ML. No subscriptions. No data leaves your machine.

## Writing

- [I stopped asking a model to read my invoices](https://dev.to/aurum_revenue/i-stopped-asking-a-model-to-read-my-invoices-3985) — why I traded a hosted model for regex, what the extractor deliberately misses, and the ten assertions behind it.
