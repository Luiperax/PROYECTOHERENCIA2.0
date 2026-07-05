#!/usr/bin/env python3
"""Descarga los datos del Mundial 2026 desde la API oficial de la FIFA y genera
data.json (partidos + detalle de goles/asistencias/tarjetas). Pensado para
ejecutarse en GitHub Actions cada pocos minutos, de modo que la web se actualice
en el servidor y funcione en cualquier navegador (incluso con bloqueadores).
"""
import json, re, sys, time, urllib.request, os

CID, SID, LANG = "17", "285023", "es"
BASE = "https://api.fifa.com/api/v3"
OUT = os.path.join(os.path.dirname(__file__), "..", "data.json")

def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503): time.sleep(2 * (i + 1)); continue
            return None
        except Exception:
            time.sleep(2); continue
    return None

def nm(o, f="TeamName"):
    if not o: return ""
    v = o.get(f)
    if not v: return ""
    if isinstance(v, str): return v
    return v[0].get("Description", "") if v else ""

STAGE_SHORT = {
    "Primera fase": "Grupos", "Dieciseisavos de final": "Dieciseisavos",
    "Octavos de final": "Octavos", "Cuartos de final": "Cuartos",
    "Semifinal": "Semifinal", "Partido por el tercer puesto": "Tercer puesto", "Final": "Final",
}

def parse_name(desc):
    m = re.search(r"\bde\s+(.+?)\s*\(", desc)
    if m: return m.group(1).strip()
    m = re.search(r"Asistencia de\s+(.+?)\.?$", desc)
    if m: return m.group(1).strip()
    m = re.search(r"^¡?\s*([^(]+?)\s*\(", desc)
    if m: return m.group(1).strip()
    return None

def main():
    cal = get(f"{BASE}/calendar/matches?idCompetition={CID}&idSeason={SID}&language={LANG}&count=500")
    if not cal or not cal.get("Results"):
        print("No se pudo obtener el calendario", file=sys.stderr); sys.exit(1)
    res = cal["Results"]

    idteam2code, code2name = {}, {}
    for m in res:
        for side in ("Home", "Away"):
            o = m.get(side)
            if o and o.get("IdTeam") and o.get("IdCountry"):
                idteam2code[o["IdTeam"]] = o["IdCountry"]
                code2name[o["IdCountry"]] = nm(o)

    matches = []
    for m in res:
        stg = nm(m, "StageName")
        matches.append({
            "id": m["IdMatch"], "stage": m["IdStage"],
            "g": (nm(m, "GroupName") or "").replace("Grupo ", ""),
            "st": STAGE_SHORT.get(stg, stg), "md": m.get("MatchDay"),
            "dt": m.get("Date"), "s": m.get("MatchStatus"), "min": m.get("MatchTime"),
            "h": nm(m.get("Home")) or nm(m, "PlaceHolderA"),
            "a": nm(m.get("Away")) or nm(m, "PlaceHolderB"),
            "hc": (m.get("Home") or {}).get("IdCountry"), "ac": (m.get("Away") or {}).get("IdCountry"),
            "hs": m.get("HomeTeamScore"), "as": m.get("AwayTeamScore"),
            "hp": m.get("HomeTeamPenaltyScore"), "ap": m.get("AwayTeamPenaltyScore"),
            "v": nm(m.get("Stadium"), "Name"), "c": nm(m.get("Stadium"), "CityName"),
        })
    matches.sort(key=lambda x: x["dt"] or "")

    timelines = {}
    for m in matches:
        if m["s"] not in (0, 3):  # solo jugados o en directo
            continue
        tl = get(f"{BASE}/timelines/{CID}/{SID}/{m['stage']}/{m['id']}?language={LANG}")
        evs = []
        if tl and tl.get("Event"):
            for e in tl["Event"]:
                d = e.get("TypeLocalized")
                d = d[0]["Description"] if d else ""
                low = d.lower()
                if "gol" in low: k = "goal"
                elif "asistencia" in low: k = "assist"
                elif "tarjeta" in low: k = "card"
                else: continue
                desc = e.get("EventDescription")
                desc = desc[0]["Description"] if desc else ""
                evs.append({"k": k, "t": e.get("MatchMinute"), "d": d,
                            "p": parse_name(desc), "tc": idteam2code.get(e.get("IdTeam")),
                            "own": 1 if "propia" in desc.lower() else 0})
        timelines[m["id"]] = evs
        time.sleep(0.2)

    data = {"matches": matches, "timelines": timelines, "code2name": code2name,
            "updated": int(time.time())}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    played = sum(1 for m in matches if m["s"] == 0)
    print(f"OK: {len(matches)} partidos ({played} jugados), {len(timelines)} con detalle")

if __name__ == "__main__":
    main()
