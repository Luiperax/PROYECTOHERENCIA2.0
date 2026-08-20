#!/usr/bin/env python3
"""Descarga LaLiga, Copa del Rey y Champions League y genera data.json.

Fuente: la API pública de ESPN (la misma que usa su propia web; sin clave ni
cabeceras especiales). Frente al proveedor anterior aporta lo que faltaba:

  - Goles y **asistencias completos** de cada partido, por jugador.
  - Estadísticas de equipo (posesión, remates, córners, pases…).
  - Muchos más partidos (la Copa del Rey pasa de ~50 a ~140 por edición).
  - Consultas por rango de fechas, así que hacen falta muchas menos peticiones.

Pensado para GitHub Actions: reutiliza el data.json anterior y solo pide lo
que falta, de modo que cada ejecución programada sea corta.
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data.json")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# Cuántos resúmenes de partido nuevos se bajan como máximo en cada ejecución.
# El resto entra en las siguientes: el objetivo es que un run programado no se eternice.
MAX_NEW_SUMMARIES = 120

COMPETITIONS = [
    {"id": "laliga", "name": "LaLiga", "emoji": "🇪🇸", "codes": ["esp.1"], "cup": False},
    {"id": "copa", "name": "Copa del Rey", "emoji": "🏆", "codes": ["esp.copa_del_rey"], "cup": True},
    {"id": "ucl", "name": "Champions League", "emoji": "⭐",
     "codes": ["uefa.champions_qual", "uefa.champions"], "cup": True},
]

ROUND_ES = {
    "round-of-32": "Dieciseisavos", "round-of-16": "Octavos de final",
    "quarterfinals": "Cuartos de final", "semifinals": "Semifinal", "final": "Final",
    "playoff-round": "Play-offs", "league-phase": "Fase de liga",
    "1st-qualifying-round": "1ª ronda previa", "2nd-qualifying-round": "2ª ronda previa",
    "3rd-qualifying-round": "3ª ronda previa", "knockout-round-play-offs": "Play-off eliminatorio",
    "first-round": "Primera eliminatoria", "second-round": "Segunda eliminatoria",
    "third-round": "Tercera eliminatoria", "preliminary-round": "Ronda previa",
    "qualifying-round": "Ronda clasificatoria",
}

# En Champions esas mismas rondas son fases previas, no eliminatorias del torneo.
ROUND_ES_UCL = {
    "first-round": "1ª ronda previa", "second-round": "2ª ronda previa",
    "third-round": "3ª ronda previa", "qualifying-round": "Ronda previa",
}

STAT_ES = {
    "possessionPct": "Posesión (%)", "totalShots": "Remates", "shotsOnTarget": "Remates a puerta",
    "wonCorners": "Córners", "foulsCommitted": "Faltas", "offsides": "Fueras de juego",
    "saves": "Paradas", "yellowCards": "Tarjetas amarillas", "redCards": "Tarjetas rojas",
    "accuratePasses": "Pases acertados", "totalPasses": "Pases totales",
}
STAT_ORDER = ["possessionPct", "totalShots", "shotsOnTarget", "wonCorners",
              "foulsCommitted", "offsides", "saves", "accuratePasses"]


def get(url, tries=4):
    for i in range(tries):
        try:
            # Sin User-Agent de navegador: con algunos ESPN responde 403.
            req = urllib.request.Request(url)
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(min(20, 2 ** (i + 1)))
                continue
            return None
        except Exception:
            time.sleep(1.5)
            continue
    return None


def load_prev():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def season_label(d, offset=0):
    """Temporada estilo '2026-2027'. La europea arranca en julio."""
    y = d.year if d.month >= 7 else d.year - 1
    y += offset
    return f"{y}-{y + 1}"


def season_bounds(season):
    start_year = int(season.split("-")[0])
    return date(start_year, 7, 1), date(start_year + 1, 6, 30)


def month_chunks(start, end):
    """Trocea el rango en tramos de ~1 mes para las consultas por fechas."""
    cur = start
    while cur <= end:
        nxt = min(end, cur + timedelta(days=30))
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def fmt(d):
    return d.strftime("%Y%m%d")


# --------------------------------------------------------------------------
def parse_event(ev, cup, comp_id=None):
    comp = (ev.get("competitions") or [{}])[0]
    cs = comp.get("competitors") or []
    home = next((c for c in cs if c.get("homeAway") == "home"), None)
    away = next((c for c in cs if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None
    status = ((ev.get("status") or {}).get("type") or {})
    venue = comp.get("venue") or {}
    slug = (ev.get("season") or {}).get("slug") or ""
    table = ROUND_ES_UCL if comp_id == "ucl" else {}
    rdn = (table.get(slug) or ROUND_ES.get(slug)
           or slug.replace("-", " ").capitalize()) if cup else ""

    def score(c):
        v = c.get("score")
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    completed = bool(status.get("completed"))
    state = status.get("state")  # pre / in / post
    return {
        "id": str(ev["id"]),
        "dt": (ev.get("date") or "")[:10],
        "time": (ev.get("date") or "")[11:16],
        "rd": slug if cup else "", "rdn": rdn,
        "h": home["team"].get("displayName"), "a": away["team"].get("displayName"),
        "hb": home["team"].get("logo"), "ab": away["team"].get("logo"),
        "hs": score(home) if completed or state == "in" else None,
        "as": score(away) if completed or state == "in" else None,
        "st": "FT" if completed else ("LIVE" if state == "in" else ""),
        "v": venue.get("fullName") or "",
        "c": ((venue.get("address") or {}).get("city") or ""),
        "_code": None,  # se rellena fuera: hace falta para pedir el resumen
    }


def fetch_matches(codes, start, end, cup, comp_id=None):
    matches = {}
    for code in codes:
        for a, b in month_chunks(start, end):
            d = get(f"{ESPN}/{code}/scoreboard?dates={fmt(a)}-{fmt(b)}&limit=300")
            for ev in ((d or {}).get("events") or []):
                m = parse_event(ev, cup, comp_id)
                if m:
                    m["_code"] = code
                    matches[m["id"]] = m
            time.sleep(0.25)
    return matches


def fetch_summary(code, mid):
    """Eventos del partido, estadísticas de equipo y goles/asistencias por jugador."""
    d = get(f"{ESPN}/{code}/summary?event={mid}")
    if not d:
        return None, None, None
    comp = ((d.get("header") or {}).get("competitions") or [{}])[0]

    events = []
    for x in (comp.get("details") or []):
        who = [p.get("athlete", {}).get("displayName")
               for p in (x.get("participants") or []) if p.get("athlete")]
        team = (x.get("team") or {}).get("displayName")
        minute = (x.get("clock") or {}).get("displayValue") or ""
        if x.get("scoringPlay"):
            events.append({"k": "goal", "t": minute, "p": who[0] if who else "",
                           "as": who[1] if len(who) > 1 else None, "tm": team,
                           "d": "penalty" if x.get("penaltyKick") else ("own" if x.get("ownGoal") else ""),
                           "own": 1 if x.get("ownGoal") else 0})
        elif x.get("redCard") or x.get("yellowCard"):
            events.append({"k": "card", "t": minute, "p": who[0] if who else "",
                           "as": None, "tm": team,
                           "d": "roja" if x.get("redCard") else "amarilla"})
    events.sort(key=lambda e: _minute(e.get("t")))

    stats = []
    teams = (d.get("boxscore") or {}).get("teams") or []
    if len(teams) == 2:
        def val(side, name):
            for s in (teams[side].get("statistics") or []):
                if s.get("name") == name:
                    return s.get("displayValue")
            return None
        # ESPN da [local, visitante] o al revés: lo resolvemos por homeAway
        order = [0, 1]
        if (teams[0].get("homeAway") or "home") == "away":
            order = [1, 0]
        for name in STAT_ORDER:
            h, a = val(order[0], name), val(order[1], name)
            if h is not None or a is not None:
                stats.append({"n": STAT_ES.get(name, name), "h": h, "a": a})

    # goles y asistencias por jugador: la parte que antes venía incompleta
    tally = []
    for r in (d.get("rosters") or []):
        tm = (r.get("team") or {}).get("displayName")
        for p in (r.get("roster") or []):
            st = {s.get("name"): s.get("value") for s in (p.get("stats") or [])}
            g = int(st.get("totalGoals") or 0)
            a = int(st.get("goalAssists") or 0)
            if g or a:
                tally.append({"p": (p.get("athlete") or {}).get("displayName"),
                              "tm": tm, "g": g, "a": a})
    return events, stats, tally


def _minute(txt):
    if not txt:
        return 0
    total, cur = 0, ""
    for ch in str(txt):
        if ch.isdigit():
            cur += ch
        elif cur:
            total += int(cur)
            cur = ""
    return total + (int(cur) if cur else 0)


def build_edition(cfg, season, ongoing, prev_ed, budget):
    """Descarga una edición completa. `budget` limita los resúmenes nuevos."""
    start, end = season_bounds(season)
    today = date.today()
    if ongoing:
        end = min(end, today + timedelta(days=45))
    matches = fetch_matches(cfg["codes"], start, end, cfg["cup"], cfg["id"])

    prev_tl = prev_ed.get("timelines") or {}
    prev_st = prev_ed.get("stats") or {}
    prev_tally = prev_ed.get("_tally") or {}

    timelines, stats, tally = {}, {}, {}
    pending = []
    for mid, m in matches.items():
        if m["st"] != "FT":
            continue
        if mid in prev_tl and mid in prev_tally:
            timelines[mid] = prev_tl[mid]
            if mid in prev_st:
                stats[mid] = prev_st[mid]
            tally[mid] = prev_tally[mid]
        else:
            pending.append(mid)

    pending.sort(key=lambda i: matches[i].get("dt") or "", reverse=True)
    used = 0
    for mid in pending:
        if used >= budget:
            break
        evs, sts, tly = fetch_summary(matches[mid]["_code"], mid)
        if evs is None:
            continue
        timelines[mid] = evs
        if sts:
            stats[mid] = sts
        tally[mid] = tly
        used += 1
        time.sleep(0.25)

    # Goles y asistencias: preferimos las estadísticas por jugador, pero en muchos
    # partidos (sobre todo de rondas modestas de copa) ESPN no las publica. En esos
    # casos los sacamos de los propios eventos del partido, que sí traen goleador
    # y asistente, para que los rankings no se queden cojos.
    goals, assists = {}, {}
    for mid, evs in timelines.items():
        rows = tally.get(mid)
        if rows:
            for r in rows:
                key = (r["p"], r["tm"])
                if r.get("g"):
                    goals[key] = goals.get(key, 0) + r["g"]
                if r.get("a"):
                    assists[key] = assists.get(key, 0) + r["a"]
            continue
        for e in (evs or []):
            if e.get("k") != "goal":
                continue
            if e.get("p") and not e.get("own"):
                key = (e["p"], e.get("tm"))
                goals[key] = goals.get(key, 0) + 1
            if e.get("as"):
                key = (e["as"], e.get("tm"))
                assists[key] = assists.get(key, 0) + 1
    mk = lambda dd: [{"p": k[0], "tm": k[1], "n": v}
                     for k, v in sorted(dd.items(), key=lambda x: (-x[1], x[0][0]))]

    for m in matches.values():
        m.pop("_code", None)
    return {
        "season": season, "ongoing": ongoing,
        "matches": sorted(matches.values(), key=lambda x: (x["dt"] or "", x["time"] or "")),
        "timelines": timelines, "stats": stats,
        "scorers": mk(goals), "assists": mk(assists),
        "_tally": tally,
    }, used


def edition_has_matches(cfg, season):
    start, end = season_bounds(season)
    end = min(end, date.today() + timedelta(days=45))
    for code in cfg["codes"]:
        for a, b in month_chunks(start, end):
            d = get(f"{ESPN}/{code}/scoreboard?dates={fmt(a)}-{fmt(b)}&limit=5")
            if (d or {}).get("events"):
                return True
            time.sleep(0.2)
    return False


def main():
    prev_all = load_prev()
    prev_comps = {c["id"]: c for c in (prev_all.get("competitions") or [])}
    today = date.today()
    comps = []
    budget = MAX_NEW_SUMMARIES

    for cfg in COMPETITIONS:
        prev = prev_comps.get(cfg["id"], {})
        prev_eds = {e["season"]: e for e in (prev.get("editions") or [])}
        current = season_label(today)
        editions = []

        if edition_has_matches(cfg, current):
            ed, used = build_edition(cfg, current, True, prev_eds.get(current, {}), budget)
            budget -= used
            editions.append(ed)

        # En las copas pasan meses entre ediciones: mientras la nueva no haya
        # arrancado de verdad conservamos la anterior para no dejar la página vacía.
        played = sum(1 for m in (editions[0]["matches"] if editions else []) if m["st"] == "FT")
        if not editions or (cfg["cup"] and played < 10):
            previous = season_label(today, -1)
            if edition_has_matches(cfg, previous):
                ed, used = build_edition(cfg, previous, False,
                                         prev_eds.get(previous, {}), max(budget, 0))
                budget -= used
                editions.append(ed)

        if not editions:
            if prev:
                comps.append(prev)
            continue

        comps.append({"id": cfg["id"], "name": cfg["name"], "emoji": cfg["emoji"],
                      "partial": False,
                      "season": editions[0]["season"], "ongoing": editions[0]["ongoing"],
                      "editions": editions})
        print(f"{cfg['name']}: " + " | ".join(
            f"{e['season']}{'' if e['ongoing'] else ' (última disputada)'}: "
            f"{len(e['matches'])} partidos, {len(e['timelines'])} con detalle, "
            f"{len(e['scorers'])} goleadores, {len(e['assists'])} asistentes"
            for e in editions), file=sys.stderr)

    data = {"competitions": comps, "updated": int(time.time())}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("OK ->", os.path.relpath(OUT))


if __name__ == "__main__":
    main()
