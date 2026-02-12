import json
import re
import requests
from bs4 import BeautifulSoup

UA = "VP-LabelGenerator/1.0 (Store label automation)"

def clean_spaces(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", (s or "")).strip()

def main(req):
    try:
        # parse varenr fra querystring eller body
        if req.method == "GET":
            varenr = req.params.get("varenr")
        else:
            body = req.get_json()
            varenr = body.get("varenr")

        if not varenr:
            return {"error": "missing varenr"}, 400

        varenr = re.sub(r"\D", "", str(varenr))
        if not varenr:
            return {"error": "invalid varenr"}, 400

        # hent produktsiden
        url = f"https://www.vinmonopolet.no/p/{varenr}"
        r = requests.get(url, timeout=20, headers={"User-Agent": UA})
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
            "productType": "[MÅ FYLLES]",
            "style": "[MÅ FYLLES]",
            "desc": "[MÅ FYLLES]"
        }

        m = re.search(r"\bKr\s*([0-9\s]+\,[0-9]{2})\b", text)
        if m: out["price"] = m.group(1).strip()

        m = re.search(r"\b(\d{2,3})\s*cl\b", text)
        if m: out["volume"] = f"{m.group(1)} cl"

        m = re.search(r"\b([0-9]+\,[0-9]{2})\s*kr/l\b", text, re.IGNORECASE)
        if m: out["krl"] = f"{m.group(1)} kr/l"

        m = re.search(r"\bAlkohol\s*([0-9]+\,[0-9])%", text, re.IGNORECASE)
        if m: out["alcohol"] = f"{m.group(1)}%"

        # sukker
        m = re.search(r"Sukker\s*Under\s*(\d+)", text)
        if m:
            out["sugar"] = f"<{m.group(1)} g/l"
        else:
            m = re.search(r"Sukker\s*([0-9]+\,[0-9])\s*g/l", text)
            if m:
                out["sugar"] = f"{m.group(1)} g/l"

        m = re.search(r"Varetype\s*([A-Za-zæøåÆØÅ ]+)", text)
        if m: out["productType"] = clean_spaces(m.group(1))

        m = re.search(r"Land,\s*distrikt\s*([^,]+),\s*([^,]+),\s*([^,]+)", text)
        if m:
            out["country"] = clean_spaces(m.group(1))
            out["district"] = clean_spaces(m.group(2)) + ", " + clean_spaces(m.group(3))

        return out, 200

    except Exception as e:
        return {"error": str(e)}, 500
