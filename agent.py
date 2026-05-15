"""
RescueAI — Heartbeat Agent
Run this on the volunteer's field device (laptop, tablet, Raspberry Pi).
It periodically pings the FastAPI server so the system knows they're alive.

Usage:
    python agent.py --id V001 --server http://192.168.1.100:8000 --interval 30

For a device with GPS (e.g. RPi + GPS hat):
    python agent.py --id V001 --server http://HQ_IP:8000 --gps
"""

import argparse
import time
import requests
import socket
import platform
import uuid
import json
import os
from datetime import datetime

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="RescueAI Heartbeat Agent")
parser.add_argument("--id",       required=True,                       help="Volunteer ID, e.g. V001")
parser.add_argument("--server",   default="http://localhost:8000",     help="FastAPI server URL")
parser.add_argument("--interval", type=int, default=30,                help="Ping interval in seconds")
parser.add_argument("--status",   default="🟢 All clear — on patrol",  help="Initial field status")
parser.add_argument("--gps",      action="store_true",                 help="Try to read GPS from gpsd")
args = parser.parse_args()

# ── Device fingerprint (stable across reboots) ────────────────────────────────
DEVICE_ID_FILE = ".rescue_device_id"

def get_device_id() -> str:
    if os.path.exists(DEVICE_ID_FILE):
        return open(DEVICE_ID_FILE).read().strip()
    # Generate from MAC + hostname for stability
    mac  = uuid.getnode()
    host = platform.node()
    did  = f"{host}-{mac:012x}"[:32]
    open(DEVICE_ID_FILE, "w").write(did)
    return did

DEVICE_ID = get_device_id()

# ── GPS (optional — requires gpsd + gpsd-py3) ─────────────────────────────────
def get_gps_coords():
    """Read lat/lon from gpsd. Returns (lat, lon) or (None, None)."""
    try:
        import gpsd
        gpsd.connect()
        lat, lon = gpsd.get_current().position()
        return round(lat, 6), round(lon, 6)
    except Exception:
        pass
    return None, None

# ── Status prompt (interactive, optional) ────────────────────────────────────
STATUS_OPTIONS = [
    "🟢 All clear — on patrol",
    "🔍 Actively searching",
    "🚨 Need backup",
    "⚠️  Lost contact with team",
    "🏥 Medical situation",
    "✅ Target located",
    "🔋 Low battery / heading back",
]

current_status = args.status

def prompt_status_update():
    """Non-blocking status update via stdin (runs in background thread)."""
    global current_status
    import threading

    def _loop():
        global current_status
        while True:
            print("\n[Agent] Update your status? (Enter number or press Enter to skip):")
            for i, s in enumerate(STATUS_OPTIONS, 1):
                print(f"  {i}. {s}")
            try:
                choice = input("Choice: ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(STATUS_OPTIONS):
                        current_status = STATUS_OPTIONS[idx]
                        print(f"[Agent] Status updated: {current_status}")
            except (EOFError, KeyboardInterrupt):
                break

    t = threading.Thread(target=_loop, daemon=True)
    t.start()

# ── Register once on startup ──────────────────────────────────────────────────
def register():
    try:
        r = requests.post(
            f"{args.server}/register",
            json={"volunteer_id": args.id, "name": args.id, "interval_sec": args.interval},
            timeout=5,
        )
        print(f"[Agent] Registered: {r.json()}")
    except Exception as e:
        print(f"[Agent] Registration failed (server offline?): {e}")

# ── Heartbeat loop ─────────────────────────────────────────────────────────────
def send_heartbeat(lat=None, lon=None):
    payload = {
        "volunteer_id": args.id,
        "device_id":    DEVICE_ID,
        "source":       "agent",
        "interval_sec": args.interval,
        "field_status": current_status,
        "lat":          lat,
        "lon":          lon,
    }
    try:
        r = requests.post(
            f"{args.server}/heartbeat",
            json=payload,
            timeout=5,
        )
        ts = datetime.now().strftime("%H:%M:%S")
        gps_str = f"  GPS: {lat:.5f}, {lon:.5f}" if lat else ""
        print(f"[{ts}] ✅ Heartbeat sent  |  status: {current_status}{gps_str}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Server unreachable — will retry in {args.interval}s")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")
        return False


def main():
    print(f"""
╔══════════════════════════════════════════════╗
║         RescueAI Heartbeat Agent             ║
╠══════════════════════════════════════════════╣
║  Volunteer : {args.id:<31}║
║  Server    : {args.server:<31}║
║  Interval  : {args.interval}s{' '*(30-len(str(args.interval)))}║
║  Device ID : {DEVICE_ID[:31]:<31}║
║  GPS mode  : {'enabled' if args.gps else 'disabled':<31}║
╚══════════════════════════════════════════════╝
Press Ctrl+C to stop.
""")

    register()
    prompt_status_update()

    consecutive_failures = 0
    while True:
        lat, lon = get_gps_coords() if args.gps else (None, None)
        success = send_heartbeat(lat=lat, lon=lon)
        consecutive_failures = 0 if success else consecutive_failures + 1

        if consecutive_failures >= 5:
            print(f"[Agent] ⚠️  {consecutive_failures} consecutive failures — is the server running?")

        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Agent] Stopped. Marking offline...")
        try:
            requests.post(f"{args.server}/offline/{args.id}", timeout=3)
            print("[Agent] Marked as offline on server.")
        except Exception:
            pass
