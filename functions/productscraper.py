import json
import re
import requests
from bs4 import BeautifulSoup

def clean_spaces(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", (s or "")).strip()

def handle_request(req):
    try:
        # GET parameter
        varenr = req.params.get("varenr")
        if not varenr:
            return {"error": "missing varenr"}, 400

        varenr = re.sub(r"\D", "", varenr)
        if not varenr:
            return {"error": "invalid varenr"}, 400

        url = f"https://www.vinmonopolet.no/p/{varenr}"
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        html = r.text

        soup = BeautifulSoup(html, "html.parser")
        text = clean_spaces(soup.get_text(" ", strip=True))

        out = {
            "varenr": varenr,
            "name": "[MÅ FYLLES]",
            "country": "[MÅ FYLLES]",
            "district": "[MÅ FYLLES]",
            "volume": "[MÅ FYLLES]",
            "price": "[MÅ FYLLES]",
            "krl": "[MÅ FYLLES]",
            "alcohol": "[MÅ FYLLES]",
            "sugar": "[MÅ FYLLES]",
            "productType": "[MÅ FYLLES]"
        }

        m = re.search(r"\bKr\s*([0-9\s]+\,[0-9]{2})", text)
        if m:
            out["price"] = m.group(1)

        return out, 200

    except Exception as e:
        return {"error": str(e)}, 500
