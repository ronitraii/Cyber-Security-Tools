#!/usr/bin/env python3
"""
Security_Scanner.py

Multi-domain safe scanner with enhanced XSS heuristics and professional HTML report
(includes "Potential XSS Injection Point" style findings like in your screenshot).

Usage:
  python Security_Scanner.py --domains example.com testphp.vulnweb.com --output multi_reports
  python Security_Scanner.py --domains-file domains.txt --output multi_reports --logo logo.png

Install:
  pip install requests beautifulsoup4
"""
import argparse
import base64
import json
import os
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html import escape
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

# ----- Configurable payloads/signatures/heuristics -----
BASE_MARKER = "SECSCAN"               # base marker for unique tokens
SQLI_PAYLOADS = ["' OR '1'='1", '" OR "1"="1"', "' OR 1=1 -- "]
SQL_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql",
    "unclosed quotation mark after the character string",
    "quoted string not properly terminated",
]
OPEN_REDIRECT_MARKER = "http://example.com/"

SUSPICIOUS_PARAM_NAMES = {"q", "query", "search", "term", "s", "callback", "return", "url", "next", "redirect"}


# ----- Utilities -----


def same_origin(u1, u2):
    p1 = urlparse(u1)
    p2 = urlparse(u2)
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def safe_get(session, url, **kw):
    try:
        return session.get(url, timeout=12, allow_redirects=True, **kw)
    except requests.RequestException:
        return None


# ----- Crawler -----


class EndpointDiscoverer:
    def __init__(self, base_url, max_pages=200, session=None):
        self.base_url = base_url if base_url.startswith(("http://", "https://")) else "http://" + base_url
        self.parsed_base = urlparse(self.base_url)
        self.max_pages = max_pages
        self.session = session or requests.Session()
        self.visited = set()
        self.endpoints = set()

    def extract_links(self, html, url):
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for tag in soup.find_all(["a", "form", "link", "script"]):
            href = tag.get("href") or tag.get("action")
            if not href:
                continue
            full = urljoin(url, href)
            parsed = urlparse(full)
            full = urlunparse(parsed._replace(fragment=""))
            links.add(full)
        return links

    def crawl(self):
        to_visit = [self.base_url]
        while to_visit and len(self.visited) < self.max_pages:
            url = to_visit.pop(0)
            if url in self.visited:
                continue
            resp = safe_get(self.session, url, headers={"User-Agent": "Security-Scanner/1.0"})
            self.visited.add(url)
            if not resp or resp.status_code >= 400:
                continue
            self.endpoints.add(url)
            content_type = resp.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                continue
            links = self.extract_links(resp.text, url)
            for link in links:
                if same_origin(self.base_url, link) and link not in self.visited:
                    if len(self.visited) + len(to_visit) < self.max_pages:
                        to_visit.append(link)
                    self.endpoints.add(link)
        return sorted(self.endpoints)


# ----- Scanner with enhanced heuristics -----


class VulnerabilityScanner:
    def __init__(self, session=None):
        self.session = session or requests.Session()

    def detect_query_params(self, url):
        parsed = urlparse(url)
        return {k: v for k, v in parse_qs(parsed.query).items()}

    def inject_query(self, url, param, payload):
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        qs[param] = [payload]
        new_qs = urlencode(qs, doseq=True)
        new = urlunparse(parsed._replace(query=new_qs))
        return new

    def classify_reflection_context(self, body, marker):
        """
        Return a coarse-grained classification where the marker appears:
        - 'html' : appears in HTML text nodes
        - 'attribute' : appears within an attribute (e.g., src="", href="", title="")
        - 'script' : appears inside <script>...</script>
        - 'unknown' : marker not present
        """
        if marker not in body:
            return "unknown"
        # quick checks
        # script
        if re.search(r"<script[^>]*>[^<]*" + re.escape(marker), body, flags=re.IGNORECASE | re.DOTALL):
            return "script"
        # attribute (heuristic: marker inside attr quotes within a tag)
        if re.search(r"<[a-zA-Z0-9\-]+\s[^>]*=[\"'][^\"'>]*" + re.escape(marker), body, flags=re.IGNORECASE | re.DOTALL):
            return "attribute"
        # else html
        return "html"

    def test_xss_and_heuristics(self, url):
        """
        For each query parameter:
         - send a unique benign marker token and check for reflection
         - classify the reflection context if found
         - also mark potential if parameter name is suspicious even without reflection
        Returns a list of finding dicts.
        """
        params = self.detect_query_params(url)
        findings = []
        if not params:
            return findings

        # For each param create a distinct marker to avoid cross-echo noise
        for p in params:
            unique_token = f"{BASE_MARKER}-{p}-{uuid.uuid4().hex[:8]}"
            # use a safe payload that's easy to find; keep small and benign
            payload = f"{unique_token}"
            test_url = self.inject_query(url, p, payload)
            try:
                r = self.session.get(test_url, timeout=12, allow_redirects=True)
                body = r.text if r else ""
            except requests.RequestException:
                body = ""

            if payload in body:
                ctx = self.classify_reflection_context(body, payload)
                findings.append({
                    "param": p,
                    "url": test_url,
                    "type": "reflected",
                    "context": ctx,
                    "evidence": payload,
                    "confidence": "high" if ctx != "unknown" else "medium"
                })
            else:
                # Passive heuristics: suspicious param name (eg q, search) or parameter name appears near templates
                suspicious_name = p.lower() in SUSPICIOUS_PARAM_NAMES
                # also check if the original parameter name (not value) is present in the page templates - may suggest echoing
                try:
                    resp_orig = self.session.get(url, timeout=10)
                    page_text = resp_orig.text if resp_orig else ""
                except requests.RequestException:
                    page_text = ""

                name_present = p in page_text
                if suspicious_name or name_present:
                    # mark as potential even if our payload didn't reflect
                    findings.append({
                        "param": p,
                        "url": test_url,
                        "type": "potential",
                        "context": "suspicious-name" if suspicious_name else ("name-present" if name_present else "unknown"),
                        "evidence": f"param name '{p}' considered suspicious" if suspicious_name else f"param name '{p}' appears in page template",
                        "confidence": "low"
                    })
        return findings

    def test_sqli(self, url):
        params = self.detect_query_params(url)
        findings = []
        if not params:
            return findings
        for p in params:
            for payload in SQLI_PAYLOADS:
                test_url = self.inject_query(url, p, payload)
                try:
                    r = self.session.get(test_url, timeout=10, allow_redirects=True)
                    if not r:
                        continue
                    body = r.text.lower()
                    for sig in SQL_ERRORS:
                        if sig in body:
                            findings.append({
                                "param": p,
                                "url": test_url,
                                "evidence": sig,
                                "confidence": "medium"
                            })
                            break
                except requests.RequestException:
                    continue
        return findings

    def test_open_redirect(self, url):
        params = self.detect_query_params(url)
        findings = []
        if not params:
            return findings
        for p in params:
            test_url = self.inject_query(url, p, OPEN_REDIRECT_MARKER)
            try:
                r = self.session.get(test_url, timeout=10, allow_redirects=False)
                location = r.headers.get("Location", "") if r else ""
                if OPEN_REDIRECT_MARKER in location:
                    findings.append({
                        "param": p,
                        "url": test_url,
                        "evidence": location,
                        "confidence": "high"
                    })
            except requests.RequestException:
                continue
        return findings

    def scan_endpoint(self, url):
        return {
            "url": url,
            "xss_candidates": self.test_xss_and_heuristics(url),
            "sqli": self.test_sqli(url),
            "open_redirect": self.test_open_redirect(url)
        }


# ----- Reporting: professional single-HTML (with yellow "Potential XSS" blocks) -----


def embed_logo_base64(logo_path):
    if not logo_path:
        return None
    try:
        with open(logo_path, "rb") as f:
            data = f.read()
        mime = "image/png"
        if logo_path.lower().endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))
    except Exception:
        return None


def save_aggregated_json(overall_results, outdir):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "security_scan_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(overall_results, f, indent=2)
    return path


def save_professional_html(overall_results, outdir, logo_b64=None):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "security_scan_summary.html")

    # top-level counts
    total_endpoints = sum(len(dom.get("endpoints", [])) for dom in overall_results)
    total_xss = sum(len([f for e in dom.get("endpoints", []) for f in e.get("xss_candidates", [])]) for dom in overall_results)
    total_sqli = sum(len([f for e in dom.get("endpoints", []) for f in e.get("sqli", [])]) for dom in overall_results)
    total_open = sum(len([f for e in dom.get("endpoints", []) for f in e.get("open_redirect", [])]) for dom in overall_results)
    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    css = """
    body{font-family:Arial,Helvetica,sans-serif;background:#f3f6f9;color:#1c2638;margin:0;padding:24px}
    .container{max-width:1100px;margin:20px auto;background:#fff;border-radius:12px;padding:22px;box-shadow:0 6px 30px rgba(20,30,50,0.06)}
    header{display:flex;gap:16px;align-items:center;border-bottom:1px solid #eef4fb;padding-bottom:16px;margin-bottom:16px}
    .logo{width:80px;height:80px;border-radius:10px;overflow:hidden;background:#fff;display:flex;align-items:center;justify-content:center}
    h1{margin:0;font-size:20px}
    .muted{color:#68737a;font-size:13px}
    .summary{display:flex;gap:10px;margin-top:10px}
    .card{background:#fbfdff;border:1px solid #eaf4ff;padding:10px 12px;border-radius:8px;min-width:120px;text-align:center}
    section{margin-top:18px}
    h2{font-size:16px;margin:0 0 10px 0}
    .endpoint{border:1px solid #eef4fb;border-radius:8px;padding:12px;margin-bottom:10px;background:#fff}
    .endpoint .url{font-family:monospace;font-size:13px;color:#0b4a6f}
    .finding-good{color:#0b7a4b;font-weight:600}
    .finding-none{color:#0b7a4b}
    .potential{background:#fffbe6;border-left:6px solid #ffd54a;padding:10px;border-radius:6px;margin-top:8px}
    .evidence{font-family:monospace;font-size:12px;color:#a33;word-break:break-all}
    table{width:100%;border-collapse:collapse;margin-top:8px}
    th,td{padding:8px 6px;border-bottom:1px solid #eef6fb;text-align:left;font-size:13px}
    thead th{background:#f1f8ff}
    .small{font-size:12px;color:#58606a}
    footer{margin-top:18px;color:#6b7780;font-size:13px;border-top:1px solid #eef6fb;padding-top:10px}
    """

    html = []
    html.append("<!doctype html><html><head><meta charset='utf-8'><title>Web Flaw Discovery Report</title>")
    html.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    html.append(f"<style>{css}</style></head><body><div class='container'>")

    # header
    logo_html = ""
    if logo_b64:
        logo_html = f"<div class='logo'><img src='{logo_b64}' style='width:100%;height:100%;object-fit:cover' alt='logo'></div>"
    else:
        logo_html = "<div class='logo'><svg width='52' height='52' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'><rect rx='6' width='24' height='24' fill='#2d9cdb'/><text x='50%' y='53%' font-size='9' text-anchor='middle' fill='white' font-family='Arial' dy='.3em'>SCAN</text></svg></div>"

    html.append("<header>")
    html.append(logo_html)
    html.append("<div><h1>Web Flaw Discovery Report</h1>")
    html.append(f"<div class='muted'>Passive security analysis for {len(overall_results)} domain(s). Report generated on: {escape(scan_time)}.</div>")
    html.append("<div class='summary'>")
    html.append(f"<div class='card'><div class='small'>Websites</div><strong>{len(overall_results)}</strong></div>")
    html.append(f"<div class='card'><div class='small'>Endpoints Checked</div><strong>{total_endpoints}</strong></div>")
    html.append(f"<div class='card'><div class='small'>Potential XSS Findings</div><strong>{total_xss}</strong></div>")
    html.append(f"<div class='card'><div class='small'>SQLi Findings</div><strong>{total_sqli}</strong></div>")
    html.append(f"<div class='card'><div class='small'>Open-Redirects</div><strong>{total_open}</strong></div>")
    html.append("</div></div></header>")

    # per-domain
    for i, dom in enumerate(overall_results, start=1):
        domain = dom.get("domain")
        eps = dom.get("endpoints", [])
        html.append(f"<section><h2>{escape(domain)} <span class='small'>( {len(eps)} Endpoints Checked )</span></h2>")
        # total potential per domain
        domain_potential = sum(len(e.get("xss_candidates", [])) for e in eps)
        html.append(f"<div style='color:#c43; font-weight:700; margin-bottom:8px'>Total Potential Findings: {domain_potential}</div>")

        if not eps:
            html.append("<div class='endpoint'>No endpoints discovered.</div>")
        for e in eps:
            html.append("<div class='endpoint'>")
            html.append(f"<div class='url'>{escape(e.get('url'))}</div>")
            # quick summary line
            xcount = len(e.get("xss_candidates", []))
            scount = len(e.get("sqli", []))
            ocount = len(e.get("open_redirect", []))
            if xcount + scount + ocount == 0:
                html.append("<div class='finding-none' style='margin-top:8px'>Findings: No Immediate Flaws Detected</div>")
            else:
                html.append(f"<div style='margin-top:8px'><strong>Findings:</strong></div>")

            # render XSS candidates with potential box (yellow)
            for f in e.get("xss_candidates", []):
                if f.get("type") == "reflected":
                    ctx = f.get("context", "html")
                    conf = f.get("confidence", "medium")
                    html.append("<div class='potential'>")
                    html.append(f"<strong>Potential XSS Injection Point</strong> on parameter <strong>{escape(f.get('param'))}</strong> — <span class='small'>context: {escape(ctx)}, confidence: {escape(conf)}</span>")
                    html.append(f"<div class='small' style='margin-top:6px'>Evidence: <span class='evidence'>{escape(f.get('evidence'))}</span></div>")
                    html.append("</div>")
                else:
                    # potential low-confidence heuristic
                    html.append("<div class='potential' style='border-left:6px solid #ffd54a'>")
                    html.append(f"<strong>Potential XSS (heuristic)</strong> on parameter <strong>{escape(f.get('param'))}</strong>")
                    html.append(f"<div class='small' style='margin-top:6px'>Reason: {escape(f.get('evidence'))} — confidence: {escape(f.get('confidence'))}</div>")
                    html.append("</div>")

            # SQLi details
            if e.get("sqli"):
                html.append("<div style='margin-top:8px'><strong>SQLi Findings:</strong></div>")
                html.append("<table><thead><tr><th>Param</th><th>Evidence</th></tr></thead><tbody>")
                for s in e.get("sqli", []):
                    html.append(f"<tr><td>{escape(s.get('param'))}</td><td class='evidence'>{escape(s.get('evidence'))}</td></tr>")
                html.append("</tbody></table>")

            # Open redirect details
            if e.get("open_redirect"):
                html.append("<div style='margin-top:8px'><strong>Open-Redirect Findings:</strong></div>")
                html.append("<table><thead><tr><th>Param</th><th>Location</th></tr></thead><tbody>")
                for o in e.get("open_redirect", []):
                    html.append(f"<tr><td>{escape(o.get('param'))}</td><td class='evidence'>{escape(o.get('evidence'))}</td></tr>")
                html.append("</tbody></table>")

            html.append("</div>")  # endpoint
        html.append("</section>")

    html.append("<footer>Note: This is a passive, non-destructive scan. Validate findings manually and obtain authorization before testing further.</footer>")
    html.append("</div></body></html>")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("".join(html))
    return path


# ----- Orchestration / CLI -----


def main():
    parser = argparse.ArgumentParser(description="Security_Scanner - enhanced heuristics + professional report")
    parser.add_argument("--domain", help="Single domain or base URL to scan (e.g. example.com)")
    parser.add_argument("--domains", nargs="+", help="Multiple domains (space separated), e.g. example.com foo.com")
    parser.add_argument("--domains-file", help="Path to a file with one domain/URL per line")
    parser.add_argument("--max-pages", type=int, default=200, help="Maximum pages to crawl per domain")
    parser.add_argument("--threads", type=int, default=12, help="Worker threads for scanning")
    parser.add_argument("--output", default="reports", help="Output directory for reports")
    parser.add_argument("--logo", help="Path to PNG/JPG logo to embed in the HTML header (optional)")
    args = parser.parse_args()

    # collect domains
    domains = []
    if args.domain:
        domains.append(args.domain)
    if args.domains:
        domains.extend(args.domains)
    if args.domains_file:
        try:
            with open(args.domains_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        domains.append(line)
        except Exception as exc:
            print("[!] Failed to read domains file:", exc)
            return

    if not domains:
        print("[!] No domains provided. Use --domain, --domains or --domains-file")
        return

    logo_b64 = embed_logo_base64(args.logo) if args.logo else None

    session = requests.Session()
    overall_results = []

    for domain in domains:
        print(f"\n[+] Starting scan for: {domain}")
        discoverer = EndpointDiscoverer(domain, max_pages=args.max_pages, session=session)
        endpoints = discoverer.crawl()
        print(f"[+] Found {len(endpoints)} endpoints for {domain}")

        scanner = VulnerabilityScanner(session=session)
        results = []
        domain_out = os.path.join(args.output, re.sub(r"[^A-Za-z0-9._-]", "_", domain))
        os.makedirs(domain_out, exist_ok=True)

        # scan endpoints concurrently
        with ThreadPoolExecutor(max_workers=args.threads) as ex:
            futures = {ex.submit(scanner.scan_endpoint, url): url for url in endpoints}
            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    res = fut.result()
                    results.append(res)
                    print(f"[=] Scanned {url} -> xss_candidates:{len(res['xss_candidates'])} sqli:{len(res['sqli'])} open_redirect:{len(res['open_redirect'])}")
                except Exception as exc:
                    print(f"[!] Error scanning {url}: {exc}")

        # write per-domain JSON (optional)
        try:
            with open(os.path.join(domain_out, "security_scan_report.json"), "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2)
        except Exception:
            pass

        overall_results.append({"domain": domain, "endpoints": results})

    agg_json = save_aggregated_json(overall_results, args.output)
    html = save_professional_html(overall_results, args.output, logo_b64=logo_b64)
    print(f"\n[+] Aggregated JSON report: {agg_json}")
    print(f"[+] Professional HTML summary: {html}")


if __name__ == "__main__":
    main()
