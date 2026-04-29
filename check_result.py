import requests
import os
import json
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
PRN      = "25020143011"
MKSEA    = "April 2026"          # URL-encoded automatically by requests
DBNM     = "siucore"
API_URL  = "https://siuexam.siu.edu.in/rsstd/DspSeatnum"
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "accept": "*/*",
    "referer": "https://siuexam.siu.edu.in/forms/resultview.html",
    "x-requested-with": "XMLHttpRequest",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "dnt": "1",
}

def check_result() -> dict:
    """Hit the SIU API and return parsed status."""
    params = {"dbnm": DBNM, "prn": PRN, "mksea": MKSEA}
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()

def is_declared(data: dict) -> bool:
    """
    When result is NOT declared the API returns something like:
        {"msg": "Semester - 2 Result not yet declared"}  (or similar empty/error response)

    When result IS declared it returns seat number info — a non-empty/non-error payload.
    Adjust the condition below once you observe the actual "declared" response shape.
    """
    # If the response contains a seat number field it's declared
    if data.get("SeatNum") or data.get("seatno") or data.get("seat_number"):
        return True
    # If a "msg" field explicitly says "not yet declared" it's not out yet
    msg = str(data.get("msg", "")).lower()
    if "not yet declared" in msg or "not declared" in msg:
        return False
    # Any other non-error response → treat as declared (safe-side)
    if data.get("status") == "success" or data.get("returncode") == 1:
        return True
    return False

def send_telegram(message: str):
    token   = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)

def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{now}] Checking SIU result for PRN {PRN}...")

    try:
        data = check_result()
        print(f"API response: {json.dumps(data)}")

        if is_declared(data):
            msg = (
                f"🎉 *SIU Sem-2 Result DECLARED!*\n"
                f"PRN: `{PRN}`\n"
                f"Check now → https://siuexam.siu.edu.in/forms/resultview.html\n\n"
                f"Raw response:\n`{json.dumps(data)}`"
            )
            send_telegram(msg)
            print("✅ Result declared — Telegram notification sent!")
        else:
            print("⏳ Result not yet declared. Will check again later.")

    except Exception as e:
        err_msg = f"⚠️ SIU Checker error at {now}:\n{e}"
        print(err_msg)
        # Optional: also notify on errors so you know the script is alive
        try:
            send_telegram(err_msg)
        except Exception:
            pass

if __name__ == "__main__":
    main()
