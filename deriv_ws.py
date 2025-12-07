# deriv_ws.py
# Background websocket price collector for Deriv (simple per-pair connections)
import threading
import time
import json
import os
from websocket import WebSocketApp

# Friendly -> Deriv symbol mapping (Forex)
PAIRS = {
    "EURUSD": "frxEURUSD",
    "USDJPY": "frxUSDJPY",
    "GBPUSD": "frxGBPUSD"
}

DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
WS_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={DERIV_APP_ID}"

# store last N ticks per symbol
price_store = {sym: [] for sym in PAIRS.keys()}
MAX_TICKS = 500

_lock = threading.Lock()

def _on_message(ws, message):
    try:
        data = json.loads(message)
        if "tick" in data:
            tick = data["tick"]
            quote = float(tick.get("quote", 0.0))
            friendly = getattr(ws, "subscribed_symbol", None)
            if friendly:
                with _lock:
                    arr = price_store.get(friendly, [])
                    arr.append(quote)
                    if len(arr) > MAX_TICKS:
                        arr.pop(0)
                    price_store[friendly] = arr
    except Exception:
        pass

def _on_error(ws, error):
    # keep silent — logs may appear on Railway logs
    print("Deriv WS error:", error)

def _on_close(ws, close_status_code, close_msg):
    print("Deriv WS closed", close_status_code, close_msg)

def start_pair_ws(friendly_symbol):
    deriv_sym = PAIRS[friendly_symbol]
    def on_open(ws):
        ws.subscribed_symbol = friendly_symbol
        # subscribe to ticks
        req = {"ticks": deriv_sym}
        ws.send(json.dumps(req))

    ws = WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=_on_message,
        on_error=_on_error,
        on_close=_on_close
    )
    ws.run_forever()

def start_all():
    # start a daemon thread per pair
    for friendly in PAIRS.keys():
        t = threading.Thread(target=start_pair_ws, args=(friendly,), daemon=True)
        t.start()
        time.sleep(0.15)

def get_recent_prices(friendly, n=100):
    with _lock:
        arr = price_store.get(friendly, [])[:]
    if not arr:
        return []
    return arr[-n:]
