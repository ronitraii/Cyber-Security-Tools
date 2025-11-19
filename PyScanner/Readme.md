# ⚡ PyScan — Multi-threaded Port Scanner (0 → 1)

**PyScan** is a lightweight, educational command-line port scanner written in Python.
It performs multi-threaded TCP connect scans, does basic banner grabbing, and exports
results to CSV, JSON, and PDF. PyScan is built for learning and small, authorized reconnaissance tasks.

---

## Table of Contents
1. Overview  
2. Features  
3. Requirements  
4. Installation (0 → 1)  
5. Usage (interactive)  
6. Example workflow  
7. Output formats  
8. CLI / Menu options (what you can configure)  
9. Safety, ethics & legal  
10. Development & contribution  
11. License

---

## 1. Overview
PyScan demonstrates core scanning concepts: multi-threading, TCP connect scanning,
concurrent socket usage, and banner grabbing. It is not intended to replace
advanced tools like Nmap — rather it is an educational implementation.

---

## 2. Features
- Multi-threaded scanning (default threads: 50)  
- TCP connect scan (socket-level)  
- Banner grabbing for service identification (where possible)  
- Menu-driven CLI for easy configuration (no complex flags required)  
- Export results to **CSV**, **JSON**, and **PDF** (via `fpdf2`)  
- Clear, human-readable results and timestamps

---

## 3. Requirements
- Python 3.8 or newer  
- `fpdf2` (for PDF export)

Recommended to use a virtual environment.

---

## 4. Installation (0 → 1)
```bash
# 1. Clone repository (if remote)
git clone https://github.com/<your-username>/Cyber-Security-Tools.git
cd Cyber-Security-Tools/PyScan

# 2. Create and activate virtual environment (recommended)
python3 -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
