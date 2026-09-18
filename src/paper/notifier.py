"""
[PURPOSE]: Webhook Notification Service (Telegram / Discord).
[DEPENDENCIES]: urllib.request.
"""

import json
import urllib.request

def send_telegram_alert(bot_token: str, chat_id: str, message: str) -> bool:
    """
    [PURPOSE]: Send text alert notification to Telegram chat.
    [DEPENDENCIES]: urllib.request.
    [ARGS]: bot_token — Telegram Bot API token; chat_id — target chat ID; message — text string.
    [RETURNS]: Boolean success flag.
    [SIDE EFFECTS]: Network HTTP POST request.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status == 200
    except Exception:
        return False
