import requests
import os
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
PRN     = "25020143011"
MKSEA   = "April 2026"      # requests will URL-encode the space → April%202026
DBNM    = "siucore"
API_URL = "https://siuexam.siu.edu.in/rsstd/DspSeatnum"
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
}

def check_result() -> str:
    """Call the SIU API and return raw response text (plain text, not JSON)."""
    params = {"dbnm": DBNM, "prn": PRN, "mksea": MKSEA}
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text.strip()

def is_declared(text: str) -> bool:
    """
    NOT declared → API returns: "Semester - 2 Result not yet declared"
    DECLARED     → API returns anything else (seat number, student info, etc.)
    """
    return "not yet declared" not in text.lower()

def send_telegram(message: str):
    token   = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    print(chat_id)
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": message},
        timeout=10,
    )

def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{now}] Checking SIU result for PRN {PRN}...")

    try:
        response_text = check_result()
        print(f"API response: {repr(response_text)}")

        if is_declared(response_text):
            msg = (
                f"SIU Sem-2 Result DECLARED!\n"
                f"PRN: {PRN}\n"
                f"Check now: https://siuexam.siu.edu.in/forms/resultview.html\n\n"
                f"API said: {response_text}"
            )
            send_telegram(msg)
            print("Result declared — Telegram notification sent!")
        else:
            send_telegram("Not Yet Declared: SIU Sem-2 Result is still not declared. Will check again later.")
            print("Result not yet declared. Will check again later.")

    except Exception as e:
        err_msg = f"SIU Checker error at {now}: {e}"
        print(err_msg)
        try:
            send_telegram(f"WARNING: {err_msg}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
