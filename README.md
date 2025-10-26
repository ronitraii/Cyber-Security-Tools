# Cyber-Security-Tools

A curated collection of safe, educational, and practical Python-based cybersecurity tools for reconnaissance and web testing.  
This repository contains multiple standalone tools, each in its own folder, with clear usage instructions and sample output.

## Included Tools

### Security_Scanner
A multi-domain, safe web vulnerability scanner that discovers endpoints and detects indicators for:
- Reflected XSS (with heuristic context classification)
- SQL injection indicators (non-destructive)
- Open redirects

Outputs a professional HTML report and a consolidated JSON report.

Folder: `Security_Scanner/`

### PyScan
A multi-threaded port scanner focused on educational network reconnaissance:
- Multi-threaded TCP connect scanning
- Banner grabbing for service identification
- Menu-driven CLI
- CSV/JSON and PDF reporting (uses fpdf2)

Folder: `PyScan/`

## Repository Layout

