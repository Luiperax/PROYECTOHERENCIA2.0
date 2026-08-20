#!/usr/bin/env python3
"""Descarga datos de LaLiga, Copa del Rey y UEFA Champions League y genera data.json.

Fuentes:
  - LaLiga y Copa del Rey: TheSportsDB (recorrido día a día, que es la única forma
    de esquivar el tope de 5 resultados por consulta de la clave gratuita).
  - Champions League: API pública oficial de la UEFA (partidos, goleadores con nombre,
    estadísticas de equipo por partido y ranking oficial de asistencias).

Pensado para ejecutarse en GitHub Actions: reutiliza el data.json anterior y solo
vuelve a pedir los días recientes o con partidos sin terminar, de modo que la
ejecución periódica sea rápida.
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import date, timedelta, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data.json")

TSDB = "https://www.thesportsdb.com/api/v1/json/3"
UEFA_MATCH = "https://match.uefa.com/v5"
UEFA_STATS = "https://matchstats.uefa.com/v1"
UEFA_COMP = "https://compstats.uefa.com/v1"

FINISHED_TSDB = {"FT", "AET", "PEN", "AP", "FT_PEN", "Match Finished"}


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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


# --------------------------------------------------------------------------
# TheSportsDB: LaLiga y Copa del Rey
# --------------------------------------------------------------------------
CUP_ROUNDS = {
    "400": "Primera eliminatoria", "500": "Ronda previa", "0": "Ronda previa",
    "256": "Dieciseisavos", "150": "Segunda eliminatoria", "125": "Segunda eliminatoria",
    "128": "Treintaidosavos", "64": "Dieciseisavos", "32": "Dieciseisavos",
    "16": "Octavos de final", "8": "Cuartos de final", "4": "Semifinal",
    "2": "Final", "1": "Final", "200": "Tercera eliminatoria",
}


def round_name(rd, is_cup):
    rd = str(rd or "")
    if is_cup:
        return CUP_ROUNDS.get(rd, "Eliminatoria " + rd if rd else "Eliminatoria")
    return "Jornada " + rd if rd else ""


def tsdb_match(e):
    return {
        "id": e["idEvent"],
        "dt": e.get("dateEvent"),
        "time": (e.get("strTime") or "")[:5],
        "rd": e.get("intRound"),
        "rdn": None,  # se rellena al saber si es copa
        "h": e.get("strHomeTeam"), "a": e.get("strAwayTeam"),
        "hb": e.get("strHomeTeamBadge"), "ab": e.get("strAwayTeamBadge"),
        "hs": e.get("intHomeScore"), "as": e.get("intAwayScore"),
        "st": e.get("strStatus") or "",
        "v": e.get("strVenue") or "",
    }


def is_done(m):
    return m.get("hs") is not None and m.get("as") is not None


def fetch_tsdb_league(league_id, start, end, prev, throttle=0.35):
    """Recorre día a día. Reutiliza días ya descargados cuyo contenido está cerrado."""
    prev_matches = {m["id"]: m for m in (prev.get("matches") or [])}
    prev_days = set(prev.get("_days_done") or [])
    matches, days_done = {}, []
    today = date.today()
    d = start
    while d <= end:
        ds = d.isoformat()
        # Un día pasado ya descargado y con todo terminado no hace falta repetirlo
        cached = [m for m in prev_matches.values() if m.get("dt") == ds]
        if ds in prev_days and d < today - timedelta(days=2) and cached and all(is_done(m) for m in cached):
            for m in cached:
                matches[m["id"]] = m
            days_done.append(ds)
            d += timedelta(days=1)
            continue
        r = get(f"{TSDB}/eventsday.php?d={ds}&l={league_id}")
        if r is not None:
            for e in (r.get("events") or []):
                m = tsdb_match(e)
                matches[m["id"]] = m
            days_done.append(ds)
            time.sleep(throttle)
        d += timedelta(days=1)
    return matches, days_done


def fetch_tsdb_details(matches, prev, limit_new=60):
    """Detalle por partido (goles/tarjetas) y estadísticas de equipo.
    Ojo: la clave gratuita recorta el detalle a 5 eventos por partido."""
    prev_tl = prev.get("timelines") or {}
    prev_st = prev.get("stats") or {}
    timelines, stats = {}, {}
    pending = []
    for mid, m in matches.items():
        if not is_done(m):
            continue
        if mid in prev_tl:
            timelines[mid] = prev_tl[mid]
            if mid in prev_st:
                stats[mid] = prev_st[mid]
        else:
            pending.append(mid)
    pending.sort(key=lambda i: matches[i].get("dt") or "", reverse=True)
    for mid in pending[:limit_new]:
        tl = get(f"{TSDB}/lookuptimeline.php?id={mid}")
        evs = []
        for t in ((tl or {}).get("timeline") or []):
            kind = {"Goal": "goal", "Card": "card", "subst": "sub"}.get(t.get("strTimeline"))
            if not kind:
                continue
            evs.append({
                "k": kind, "t": t.get("intTime"),
                "p": (t.get("strPlayer") or "").strip(),
                "as": (t.get("strAssist") or "").strip() or None,
                "tm": t.get("strTeam"),
                "d": t.get("strTimelineDetail") or "",
            })
        timelines[mid] = evs
        time.sleep(0.3)
        st = get(f"{TSDB}/lookupeventstats.php?id={mid}")
        rows = []
        for s in ((st or {}).get("eventstats") or []):
            rows.append({"n": s.get("strStat"), "h": s.get("intHome"), "a": s.get("intAway")})
        if rows:
            stats[mid] = rows
        time.sleep(0.3)
    return timelines, stats


# --------------------------------------------------------------------------
# UEFA: Champions League
# --------------------------------------------------------------------------
def es(obj, field, fallback=""):
    """Traducción al español si existe."""
    tr = (obj or {}).get("translations", {}).get(field, {})
    return tr.get("ES") or tr.get("EN") or fallback


def fetch_ucl(season_year, prev):
    ms = get(f"{UEFA_MATCH}/matches?competitionId=1&seasonYear={season_year}&offset=0&limit=500")
    if not isinstance(ms, list):
        return None
    matches, timelines, stats = {}, {}, {}
    prev_tl = prev.get("timelines") or {}
    prev_st = prev.get("stats") or {}
    goals = {}
    pid_name = {}

    for m in ms:
        ht, at = m.get("homeTeam") or {}, m.get("awayTeam") or {}
        sc = (m.get("score") or {}).get("total") or {}
        rd = m.get("round") or {}
        mid = str(m["id"])
        matches[mid] = {
            "id": mid,
            "dt": (m.get("kickOffTime") or {}).get("date"),
            "time": ((m.get("kickOffTime") or {}).get("dateTime") or "")[11:16],
            "rd": es(rd, "name", (rd.get("metaData") or {}).get("name") or ""),
            "rdn": es(rd, "name", (rd.get("metaData") or {}).get("name") or ""),
            "h": ht.get("internationalName"), "a": at.get("internationalName"),
            "hb": ht.get("logoUrl"), "ab": at.get("logoUrl"),
            "hs": sc.get("home"), "as": sc.get("away"),
            "st": "FT" if m.get("status") == "FINISHED" else ("LIVE" if m.get("status") == "LIVE" else ""),
            "v": (m.get("stadium") or {}).get("internationalName") or "",
        }

    finished = [mid for mid, m in matches.items() if m["st"] == "FT"]
    new = [mid for mid in finished if mid not in prev_tl]
    for mid in finished:
        if mid in prev_tl:
            timelines[mid] = prev_tl[mid]
            if mid in prev_st:
                stats[mid] = prev_st[mid]
    new.sort(key=lambda i: matches[i].get("dt") or "", reverse=True)

    for mid in new[:40]:
        d = get(f"{UEFA_MATCH}/matches/{mid}")
        evs = []
        hid = str(((d or {}).get("homeTeam") or {}).get("id") or "")
        hname = matches[mid]["h"]
        aname = matches[mid]["a"]
        for s in (((d or {}).get("playerEvents") or {}).get("scorers") or []):
            pl = s.get("player") or {}
            nm = pl.get("internationalName") or ""
            if pl.get("id"):
                pid_name[str(pl["id"])] = nm
            gtype = s.get("goalType") or ""
            own = gtype == "OWN_GOAL"
            t = s.get("time") or {}
            minute = t.get("minute") if isinstance(t, dict) else None
            scoring_team = hname if str(s.get("teamId")) == hid else aname
            evs.append({"k": "goal",
                        "t": str(minute) if minute is not None else "",
                        "p": nm, "as": None, "tm": scoring_team,
                        "d": "penalty" if gtype == "PENALTY" else ("own" if own else ""),
                        "own": 1 if own else 0})
        evs.sort(key=lambda e: int(e["t"]) if str(e["t"]).isdigit() else 0)
        timelines[mid] = evs
        time.sleep(0.2)
        ts = get(f"{UEFA_STATS}/team-statistics/{mid}")
        if isinstance(ts, list) and len(ts) == 2:
            wanted = {"total_attempts": "Remates", "ball_possession": "Posesión (%)",
                      "total_attempts_on_target": "Remates a puerta", "corners": "Córners",
                      "fouls_committed": "Faltas", "offsides": "Fueras de juego"}
            byname = []
            for key, label in wanted.items():
                def val(side):
                    for s in (ts[side].get("statistics") or []):
                        if s.get("name") == key:
                            return s.get("value")
                    return None
                h, a = val(0), val(1)
                if h is not None or a is not None:
                    byname.append({"n": label, "h": h, "a": a})
            if byname:
                stats[mid] = byname
        time.sleep(0.2)

    # goleadores desde los propios partidos (nombres incluidos)
    for mid, evs in timelines.items():
        for e in evs:
            if e.get("k") == "goal" and not e.get("own") and e.get("p"):
                goals[e["p"]] = goals.get(e["p"], 0) + 1
    scorers = [{"p": k, "n": v} for k, v in sorted(goals.items(), key=lambda x: -x[1])]

    # asistencias: ranking oficial (solo trae playerId) resuelto con los nombres que conocemos
    assists = []
    ar = get(f"{UEFA_COMP}/player-ranking?competitionId=1&seasonYear={season_year}&stats=assists&limit=60&offset=0")
    if isinstance(ar, list):
        for row in ar:
            pid = str(row.get("playerId"))
            n = None
            for s in (row.get("statistics") or []):
                if s.get("name") == "assists":
                    n = int(s.get("value") or 0)
            nm = pid_name.get(pid) or (prev.get("_pid_name") or {}).get(pid)
            if nm and n:
                assists.append({"p": nm, "n": n})
    return {"matches": matches, "timelines": timelines, "stats": stats,
            "scorers": scorers, "assists": assists, "_pid_name": pid_name}


# --------------------------------------------------------------------------
def aggregate_from_timelines(timelines):
    goals, assists = {}, {}
    for evs in timelines.values():
        for e in evs:
            if e.get("k") != "goal":
                continue
            if "own" in (e.get("d") or "").lower() or e.get("own"):
                continue
            p = e.get("p")
            if p:
                key = (p, e.get("tm"))
                goals[key] = goals.get(key, 0) + 1
            a = e.get("as")
            if a:
                key = (a, e.get("tm"))
                assists[key] = assists.get(key, 0) + 1
    mk = lambda d: [{"p": k[0], "tm": k[1], "n": v} for k, v in sorted(d.items(), key=lambda x: -x[1])]
    return mk(goals), mk(assists)


def main():
    prev_all = load_prev()
    prev_comps = {c["id"]: c for c in (prev_all.get("competitions") or [])}
    today = date.today()
    comps = []

    # ---- LaLiga ----
    lp = prev_comps.get("laliga", {})
    start = date(2026, 8, 1)
    end = min(today + timedelta(days=45), date(2027, 6, 15))
    m, days = fetch_tsdb_league("4335", start, end, lp)
    for x in m.values():
        x["rdn"] = round_name(x.get("rd"), False)
    tl, st = fetch_tsdb_details(m, lp)
    g, a = aggregate_from_timelines(tl)
    comps.append({"id": "laliga", "name": "LaLiga", "season": "2026-2027", "emoji": "🇪🇸",
                  "matches": sorted(m.values(), key=lambda x: (x["dt"] or "", x["time"] or "")),
                  "timelines": tl, "stats": st, "scorers": g, "assists": a,
                  "partial": True, "_days_done": days})
    print(f"LaLiga: {len(m)} partidos, {len(tl)} con detalle", file=sys.stderr)

    # ---- Copa del Rey ----
    cp = prev_comps.get("copa", {})
    m2, days2 = fetch_tsdb_league("4483", date(2025, 9, 1), date(2026, 5, 1), cp)
    for x in m2.values():
        x["rdn"] = round_name(x.get("rd"), True)
    tl2, st2 = fetch_tsdb_details(m2, cp, limit_new=40)
    g2, a2 = aggregate_from_timelines(tl2)
    comps.append({"id": "copa", "name": "Copa del Rey", "season": "2025-2026", "emoji": "🏆",
                  "matches": sorted(m2.values(), key=lambda x: (x["dt"] or "", x["time"] or "")),
                  "timelines": tl2, "stats": st2, "scorers": g2, "assists": a2,
                  "partial": True, "_days_done": days2})
    print(f"Copa del Rey: {len(m2)} partidos, {len(tl2)} con detalle", file=sys.stderr)

    # ---- Champions League ----
    up = prev_comps.get("ucl", {})
    u = fetch_ucl(2027, up)
    if u:
        comps.append({"id": "ucl", "name": "Champions League", "season": "2026-2027", "emoji": "⭐",
                      "matches": sorted(u["matches"].values(), key=lambda x: (x["dt"] or "", x["time"] or "")),
                      "timelines": u["timelines"], "stats": u["stats"],
                      "scorers": u["scorers"], "assists": u["assists"],
                      "partial": False, "_pid_name": u["_pid_name"]})
        print(f"Champions: {len(u['matches'])} partidos, {len(u['timelines'])} con detalle", file=sys.stderr)
    elif up:
        comps.append(up)

    data = {"competitions": comps, "updated": int(time.time())}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("OK ->", os.path.relpath(OUT))


if __name__ == "__main__":
    main()
