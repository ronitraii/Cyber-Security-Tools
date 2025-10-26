# 🔒 Security_Scanner — Multi-domain Web Flaw Discovery Tool

**Security_Scanner.py** is a safe, multi-domain web scanner that discovers endpoints and runs non-destructive checks for common web flaws. It aggregates results into a single professional HTML report and an aggregated JSON report.

---

## Table of Contents
1. Overview  
2. Features  
3. Requirements  
4. Installation  
5. Usage (examples & CLI)  
6. How checks are performed (technical notes)  
7. Output & Reporting  
8. Safety, Ethics & Limitations  
9. Development & Contribution  
10. License

---

## 1. Overview
Security_Scanner crawls provided domain(s), finds endpoints, and safely checks query parameters for indicators of Reflected XSS, SQL injection (heuristics), and open-redirect vulnerabilities. It is designed for authorized testing, lab use, and triage — not exploitation.

---

## 2. Features
- Multi-domain scanning (scan multiple domains in one run)  
- Lightweight crawler (same-origin link and form action discovery)  
- Reflected XSS detection with heuristics and context classification (script / attribute / html)  
- SQLi heuristics (error snippets and response-size heuristics)  
- Open-redirect checks (common redirect parameters)  
- Generates a **single professional HTML report** with logo area and yellow-highlighted findings  
- Aggregated `security_scan_report.json` for automation and analysis  
- Configurable via: `--domains`, `--domains-file`, `--max-pages`, `--threads`, `--logo`

---

## 3. Requirements
- Python 3.8+  
- Python packages:
  - `requests`
  - `beautifulsoup4`

Install dependencies:
```bash
pip install -r requirements.txt

python3 Security_Scanner.py --domains example.com testphp.vulnweb.com --output reports

