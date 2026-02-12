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
            varenr = (body or {}).get("varenr")

        if not varenr:
            return {"error": "missing varenr"}, 400

        varenr = re.sub(r"\D", "", str(varenr))
        if not varenr:
            return {"error": "invalid varenr"}, 400

        # hent produktsiden
        url = f"https://www.vinmonopolet.no/p/{varenr}"
        r = requests.get(url, timeout=20, headers={"User-Agent": UA})
        r.raise_for_status()
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

        # Pris
        m = re.search(r"\b[Kk]r\s*([0-9\.\s]+\,[0-9]{2})\b", text)
        if m:
            out["price"] = m.group(1).strip()

        # Volum
        m = re.search(r"\b(\d{2,3})\s*cl\b", text)
        if m:
            out["volume"] = f"{m.group(1)} cl"
        else:
            m = re.search(r"\b([0-9]+)\s*l\b", text, re.IGNORECASE)
            if m:
                out["volume"] = f"{m.group(1)} l"

        # kr/l
        m = re.search(r"\b([0-9]+\,[0-9]{2})\s*kr/l\b", text, re.IGNORECASE)
        if m:
            out["krl"] = f"{m.group(1)} kr/l"

        # Alkohol
        m = re.search(r"\bAlkohol\s*([0-9]+(?:\,[0-9])?)\s*%(\s*vol\.)?\b", text, re.IGNORECASE)
        if m:
            out["alcohol"] = f"{m.group(1)}%"

        # Sukker
        m = re.search(r"\bSukker\s*(Under|Mindre enn)\s*([0-9]+)\s*g/l\b", text, re.IGNORECASE)
        if m:
            out["sugar"] = f"<{m.group(2)} g/l"
        else:
            m = re.search(r"\bSukker\s*([0-9]+(?:\,[0-9])?)\s*g/l\b", text, re.IGNORECASE)
            if m:
                out["sugar"] = f"{m.group(1)} g/l"

        # Varetype
        m = re.search(r"\bVaretype\s*([A-Za-zÆØÅæøå \-]+)\b", text, re.IGNORECASE)
        if m:
            val = clean_spaces(m.group(1))
            out["productType"] = val[:1].upper() + val[1:] if val else out["productType"]

        # Land/distrikt
        m = re.search(r"\bLand,\s*distrikt\s*([^,]+),\s*([^,]+),\s*([^,]+)\b", text)
        if m:
            out["country"] = clean_spaces(m.group(1))
            out["district"] = f"{clean_spaces(m.group(2))}, {clean_spaces(m.group(3))}"
        else:
            m = re.search(r"\bLand,\s*distrikt\s*([^,]+),\s*([^,]+)\b", text)
            if m:
                out["country"] = clean_spaces(m.group(1))
                out["district"] = clean_spaces(m.group(2))
            else:
                m = re.search(r"\bLand\s*([^,]+)\b", text)
                if m:
                    out["country"] = clean_spaces(m.group(1))

        # Enkel beskrivelse (valgfritt)
        desc_candidates = []
        for label in ("Smak", "Aroma", "Duft", "Farge", "Produktbeskrivelse", "Beskrivelse"):
            pat = re.compile(label + r"\s*([^.]{10,300})", re.IGNORECASE)
            m = pat.search(text)
            if m:
                desc_candidates.append(f"{label}: {clean_spaces(m.group(1))}")
        if desc_candidates:
            out["desc"] = " | ".join(desc_candidates)[:500]

        return out, 200

    except requests.HTTPError as ex:
        return {"error": f"http {getattr(ex.response,'status_code',None)}"}, 502
    except Exception as e:
        return {"error": str(e)}, 500