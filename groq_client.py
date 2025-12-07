# groq_client.py
# Very small Groq REST wrapper. If GROQ_API_KEY is missing, returns None.
import os
import requests
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def groq_predict_json(market_context: str):
    """
    Send market_context to Groq and request machine-readable JSON:
    Expect JSON like: {"direction":"CALL","confidence":88,"reason":"..."}
    If GROQ_API_KEY is not set or the call fails, return None.
    """
    if not GROQ_API_KEY:
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        system = "You are a concise market analyst. Return ONLY a JSON object with keys: direction (CALL or PUT), confidence (integer 0-100), reason (short string). No extra text."
        user = f"Market snapshot: {market_context}. Return JSON."
        payload = {
            "model": "mixtral-8x7b-32768",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0.0,
            "max_tokens": 200
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()
        # extract assistant message
        msg = j.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Try to load JSON from the reply
        try:
            parsed = json.loads(msg)
            # basic validation
            if "direction" in parsed and "confidence" in parsed:
                return parsed
        except Exception:
            # Sometimes the model wraps JSON in backticks or text; attempt to extract JSON substring
            import re
            m = re.search(r"\{.*\}", msg, flags=re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                    if "direction" in parsed and "confidence" in parsed:
                        return parsed
                except Exception:
                    return None
        return None
    except Exception:
        return None
