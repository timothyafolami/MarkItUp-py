# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in MarkItUp, please report it privately to
**timmy@upstridelabs.com**. Do not open a public issue.

We aim to acknowledge reports within 48 hours and provide an initial assessment
within 5 business days.

## Scope

MarkItUp is a document generation library. Security concerns are most likely to
involve:

- Path traversal when reading markdown files, theme files, images, or `base_docx` templates
- XML/HTML injection via untrusted markdown input
- Command injection via the CLI
- Denial of service via deeply nested markdown or maliciously large inputs

## What MarkItUp does *not* do

- It does not execute user-supplied code (no `eval`, no template engine)
- It does not make network requests (except the `stamp` command reading image paths)
- It does not persist data or maintain a server
