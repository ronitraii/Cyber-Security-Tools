#!/usr/bin/env python3
"""
Keystroke Dynamics Collector & Reporter

Usage examples:
  # basic run: record keystrokes until ESC is pressed, output to reports/
  python keystroke_analyzer.py --output reports/session1

  # with Telegram summary (bot token + chat id)
  python keystroke_analyzer.py --output reports/session1 --telegram-bot-token BOT_TOKEN --telegram-chat-id CHAT_ID

  # with Discord webhook
  python keystroke_analyzer.py --output reports/session1 --discord-webhook https://discord.com/api/webhooks/...

Controls:
  - Press ESC to stop recording and generate reports.
Notes:
  - This program records keystroke timestamps while running. Use only with consent.
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from html import escape
from threading import Event, Thread

try:
    from pynput import keyboard
except Exception as e:
    print("Missing dependency: pynput. Install with `pip install pynput`")
    raise

try:
    import requests
except Exception as e:
    print("Missing dependency: requests. Install with `pip install requests`")
    raise

# ---------------------------
# Data structures and helpers
# ---------------------------

class KeystrokeSession:
    def __init__(self):
        self.events = []  # list of dicts: {type: 'down'|'up', key: str, time: float}
        self.start_time = None
        self.end_time = None

    def add_event(self, ev_type, key, t):
        if self.start_time is None:
            self.start_time = t
        self.events.append({"type": ev_type, "key": key, "time": t})

    def finalize(self):
        if self.events:
            self.end_time = self.events[-1]["time"]
        else:
            self.end_time = self.start_time = time.time()

    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def to_json(self):
        return {
            "start_time": datetime.utcfromtimestamp(self.start_time).strftime("%Y-%m-%dT%H:%M:%S.%fZ") if self.start_time else None,
            "end_time": datetime.utcfromtimestamp(self.end_time).strftime("%Y-%m-%dT%H:%M:%S.%fZ") if self.end_time else None,
            "duration_seconds": self.duration(),
            "events": self.events
        }

# ---------------------------
# Metrics calculation
# ---------------------------

def compute_metrics(session: KeystrokeSession):
    """
    Compute:
     - dwell times per key (time between key down and key up for the same key)
     - flight times between successive key down events (down -> next down)
     - aggregated statistics (count, average, min, max, stddev)
    """
    import math

    # map to store last down time per key (for dwell)
    last_down = {}
    dwell_times = defaultdict(list)

    # list of down event times (for flight)
    down_times = []

    for ev in session.events:
        if ev["type"] == "down":
            down_times.append((ev["key"], ev["time"]))
            last_down[ev["key"]] = ev["time"]
        elif ev["type"] == "up":
            k = ev["key"]
            if k in last_down:
                dt = ev["time"] - last_down[k]
                if dt >= 0:
                    dwell_times[k].append(dt)
                # remove last_down[k] to avoid repeated pairing (in case of repeats)
                last_down.pop(k, None)

    # flight times (time from a down to the next down)
    flight_times = []
    for i in range(len(down_times)-1):
        t1 = down_times[i][1]
        t2 = down_times[i+1][1]
        flight_times.append(t2 - t1)

    # helper stats
    def stats_from_list(lst):
        if not lst:
            return {"count": 0, "avg": None, "min": None, "max": None, "std": None}
        n = len(lst)
        avg = sum(lst)/n
        mn = min(lst)
        mx = max(lst)
        var = sum((x-avg)**2 for x in lst)/n
        std = math.sqrt(var)
        return {"count": n, "avg": avg, "min": mn, "max": mx, "std": std}

    # per-key stats for dwell
    per_key_stats = {}
    for k, lst in dwell_times.items():
        per_key_stats[k] = stats_from_list(lst)

    flight_stats = stats_from_list(flight_times)

    overall = {
        "duration_seconds": session.duration(),
        "total_key_events": len(session.events),
        "total_key_downs": sum(1 for e in session.events if e["type"]=="down"),
        "total_key_ups": sum(1 for e in session.events if e["type"]=="up"),
        "flight_stats": flight_stats,
        "per_key_dwell_stats": per_key_stats
    }
    return overall

# ---------------------------
# Reporting (JSON + HTML)
# ---------------------------

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Keystroke Dynamics Report - {title}</title>
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; background: #f7f9fb; color: #222; padding: 24px; }}
    .card {{ background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 6px 20px rgba(30,45,60,0.06); margin-bottom: 16px; }}
    h1 {{ margin: 0 0 8px 0; font-size: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid #eef4fb; text-align: left; }}
    thead th {{ background: #f1f8ff; }}
    .muted {{ color: #556; font-size: 13px; }}
    .mono {{ font-family: monospace; font-size: 13px; background: #fafafa; padding: 4px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Keystroke Dynamics Report — {title}</h1>
    <div class="muted">Generated: {generated}</div>
    <p>Duration: <strong>{duration:.3f} seconds</strong> · Total events: <strong>{total_events}</strong></p>
  </div>

  <div class="card">
    <h2>Summary Metrics</h2>
    <table>
      <thead><tr><th>Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Total key down events</td><td>{downs}</td></tr>
        <tr><td>Total key up events</td><td>{ups}</td></tr>
        <tr><td>Flight (down→down) — count</td><td>{flight_count}</td></tr>
        <tr><td>Flight (down→down) — avg (s)</td><td>{flight_avg}</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Per-key Dwell Time (seconds)</h2>
    <table>
      <thead><tr><th>Key</th><th>Count</th><th>Avg</th><th>Min</th><th>Max</th><th>Std</th></tr></thead>
      <tbody>
        {per_key_rows}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Raw Events (first 500 shown)</h2>
    <table>
      <thead><tr><th>#</th><th>Type</th><th>Key</th><th>Timestamp (s since epoch)</th></tr></thead>
      <tbody>
        {raw_rows}
      </tbody>
    </table>
  </div>

  <footer class="muted">Note: This report was generated by Keystroke Analyzer. Only use with explicit consent.</footer>
</body>
</html>
"""

def save_json_report(session: KeystrokeSession, metrics: dict, outpath: str):
    data = {
        "session": session.to_json(),
        "metrics": metrics,
    }
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return outpath

def save_html_report(session: KeystrokeSession, metrics: dict, outpath: str, title: str = "Session"):
    per_key_rows = []
    for k, stats in metrics["per_key_dwell_stats"].items():
        per_key_rows.append("<tr><td>{key}</td><td>{count}</td><td>{avg:.4f}</td><td>{min:.4f}</td><td>{max:.4f}</td><td>{std:.4f}</td></tr>".format(
            key=escape(str(k)), count=stats["count"], avg=stats["avg"] or 0.0, min=stats["min"] or 0.0, max=stats["max"] or 0.0, std=stats["std"] or 0.0
        ))

    # raw events preview
    raw_rows = []
    for i, ev in enumerate(session.events[:500]):
        raw_rows.append("<tr><td>{i}</td><td>{type}</td><td class='mono'>{key}</td><td>{time:.6f}</td></tr>".format(
            i=i+1, type=escape(ev["type"]), key=escape(str(ev["key"])), time=ev["time"]
        ))

    html = HTML_TEMPLATE.format(
        title=escape(title),
        generated=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        duration=metrics["duration_seconds"],
        total_events=len(session.events),
        downs=metrics.get("total_key_downs", 0),
        ups=metrics.get("total_key_ups", 0),
        flight_count=metrics.get("flight_stats", {}).get("count", 0),
        flight_avg=metrics.get("flight_stats", {}).get("avg", 0) or 0.0,
        per_key_rows="\n".join(per_key_rows) if per_key_rows else "<tr><td colspan='6'>No dwell data collected</td></tr>",
        raw_rows="\n".join(raw_rows) if raw_rows else "<tr><td colspan='4'>No events</td></tr>"
    )
    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write(html)
    return outpath

# ---------------------------
# Telemetry (optional) — Telegram & Discord
# ---------------------------

def send_telegram_summary(bot_token: str, chat_id: str, summary_text: str):
    # bot_token: '123:ABC...'
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": summary_text, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.ok, resp.text
    except Exception as e:
        return False, str(e)

def send_discord_summary(webhook_url: str, summary_text: str):
    payload = {"content": summary_text}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        return resp.ok, resp.text
    except Exception as e:
        return False, str(e)

# ---------------------------
# Keyboard listener routine
# ---------------------------

def run_collector(output_dir: str, session_name: str, telegram_bot_token=None, telegram_chat_id=None, discord_webhook=None, stop_event: Event=None):
    session = KeystrokeSession()

    def on_press(key):
        t = time.time()
        k = format_key(key)
        session.add_event("down", k, t)
        # user can press ESC to stop
        if key == keyboard.Key.esc:
            # set stop event — listener will stop
            if stop_event:
                stop_event.set()
            return False

    def on_release(key):
        t = time.time()
        k = format_key(key)
        session.add_event("up", k, t)
        # ESC release also stops (just in case)
        if key == keyboard.Key.esc:
            if stop_event:
                stop_event.set()
            return False

    print("Recording keystrokes. Press ESC to stop and generate reports.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        # block until stop_event is set (ESC)
        if stop_event:
            stop_event.wait()
            # once stop_event is set, stop listener
            listener.stop()
        else:
            listener.join()

    session.finalize()

    # compute metrics
    metrics = compute_metrics(session)

    # ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = f"{session_name}_{ts}"
    json_path = os.path.join(output_dir, f"{base}.json")
    html_path = os.path.join(output_dir, f"{base}.html")

    save_json_report(session, metrics, json_path)
    save_html_report(session, metrics, html_path, title=session_name)

    print(f"Reports written:\n  JSON -> {json_path}\n  HTML -> {html_path}")

    # optional summaries to telegram/discord
    summary_text = f"Keystroke session: *{session_name}*\nDuration: {metrics['duration_seconds']:.3f}s\nEvents: {len(session.events)}\nPotential findings: {len(metrics.get('per_key_dwell_stats', {}))} keys measured"
    if telegram_bot_token and telegram_chat_id:
        ok, resp_text = send_telegram_summary(telegram_bot_token, telegram_chat_id, summary_text)
        print(f"Telegram send: {ok} {resp_text}")
    if discord_webhook:
        ok, resp_text = send_discord_summary(discord_webhook, summary_text)
        print(f"Discord send: {ok} {resp_text}")

    return json_path, html_path

# ---------------------------
# Key formatting helper
# ---------------------------

def format_key(key):
    """Return readable representation for a pynput key"""
    try:
        if isinstance(key, keyboard.KeyCode):
            return key.char if key.char is not None else str(key)
        else:
            return str(key).replace("Key.", "")  # Key.space -> space
    except Exception:
        return str(key)

# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Keystroke dynamics collector and reporter (ethical use only)")
    parser.add_argument("--output", "-o", required=True, help="Output directory prefix (e.g. reports/session1)")
    parser.add_argument("--name", "-n", default="session", help="Session name used in report filenames")
    parser.add_argument("--telegram-bot-token", help="Telegram bot token (optional) for short summary")
    parser.add_argument("--telegram-chat-id", help="Telegram chat id (optional)")
    parser.add_argument("--discord-webhook", help="Discord webhook URL (optional) for short summary")
    parser.add_argument("--consent", action="store_true", help="Set this flag to confirm you have consent from participants")
    args = parser.parse_args()

    if not args.consent:
        print("IMPORTANT: This tool records keystrokes. You MUST have explicit consent from participants.")
        print("If you have consent, re-run with --consent flag.")
        sys.exit(1)

    # create stop event
    stop_event = Event()

    try:
        run_collector(args.output, args.name, telegram_bot_token=args.telegram_bot_token,
                      telegram_chat_id=args.telegram_chat_id, discord_webhook=args.discord_webhook,
                      stop_event=stop_event)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as exc:
        print("Error while running collector:", exc)

if __name__ == "__main__":
    main()
