import requests
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone

API_KEY = "123"
LEAGUE_ID = "4429"
SEASON = "2026"
ICS_FILE = "worldcup2026_schedule.ics"


# =========================
# 国家（核心修复：补全 + fallback）
# =========================
COUNTRIES = {
    "Mexico": ("墨西哥", "MX"),
    "United States": ("美国", "US"),
    "USA": ("美国", "US"),
    "Spain": ("西班牙", "ES"),
    "Brazil": ("巴西", "BR"),
    "France": ("法国", "FR"),
    "Argentina": ("阿根廷", "AR"),
    "Germany": ("德国", "DE"),
    "England": ("英格兰", "GB"),
    "Portugal": ("葡萄牙", "PT"),
    "Japan": ("日本", "JP"),
    "Korea Republic": ("韩国", "KR"),
    "South Korea": ("韩国", "KR"),
    "Canada": ("加拿大", "CA"),
    "Morocco": ("摩洛哥", "MA"),
    "Netherlands": ("荷兰", "NL"),
    "Belgium": ("比利时", "BE"),
    "Croatia": ("克罗地亚", "HR"),
    "Uruguay": ("乌拉圭", "UY"),
    "Colombia": ("哥伦比亚", "CO"),
    "Switzerland": ("瑞士", "CH"),
    "Denmark": ("丹麦", "DK"),
    "Sweden": ("瑞典", "SE"),
    "Norway": ("挪威", "NO"),
    "Poland": ("波兰", "PL"),
    "Serbia": ("塞尔维亚", "RS"),
    "Turkey": ("土耳其", "TR"),
    "Australia": ("澳大利亚", "AU"),
    "Saudi Arabia": ("沙特", "SA"),
    "Qatar": ("卡塔尔", "QA"),
    "Czech Republic": ("捷克", "CZ"),
    "Haiti": ("海地", "HT"),
    "Scotland": ("苏格兰", "GB"),
    "Paraguay": ("巴拉圭", "PY"),
    "Cape Verde": ("佛得角", "CV"),
}


# =========================
# 城市
# =========================
CITIES = {
    "Los Angeles": "洛杉矶",
    "New York": "纽约",
    "Dallas": "达拉斯",
    "Miami": "迈阿密",
    "Seattle": "西雅图",
    "San Francisco": "旧金山",
    "Atlanta": "亚特兰大",
    "Boston": "波士顿",
}

HOST_COUNTRIES = {
    "United States": "美国",
    "USA": "美国",
    "Canada": "加拿大",
    "Mexico": "墨西哥",
}


# =========================
# emoji（安全版）
# =========================
def emoji(code):
    if not code or len(code) < 2:
        return ""
    return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)


# =========================
# 队伍（关键修复 fallback）
# =========================
def team(name):
    if not name:
        return "待定"

    cn, code = COUNTRIES.get(name, (name, ""))
    flag = emoji(code)

    # 如果没中文映射 → 直接用英文（避免空/错乱）
    return f"{flag} {cn}" if cn else name


# =========================
# 组别（修复稳定）
# =========================
def stage(e):
    g = e.get("strGroup") or e.get("strRound") or e.get("strStage") or ""

    mapping = {
        "Group A": "A组",
        "Group B": "B组",
        "Group C": "C组",
        "Group D": "D组",
        "Group E": "E组",
        "Group F": "F组",
        "Group G": "G组",
        "Group H": "H组",
        "Round of 16": "16强",
        "Quarter-finals": "8强",
        "Semi-finals": "半决赛",
        "Final": "决赛",
    }

    return mapping.get(g, g if g else "")


# =========================
# 比分
# =========================
def score(e):
    hs = e.get("intHomeScore")
    aw = e.get("intAwayScore")
    if hs is None or aw is None:
        return None
    return f"{hs}-{aw}"


# =========================
# 状态（彻底修复）
# =========================
def match_status(e):
    status = (e.get("strStatus") or "").lower()

    if status in ["ft", "finished", "match finished"]:
        return "finished"

    if "live" in status or "in progress" in status:
        return "live"

    return "not_started"


# =========================
# 标题（最终稳定格式）
# =========================
def title(e):
    home = team(e.get("strHomeTeam"))
    away = team(e.get("strAwayTeam"))

    s = score(e)
    st = stage(e)

    if s:
        line = f"{home} {s} {away}"
    else:
        line = f"{home} vs {away}"

    if st:
        line += f" ｜{st}"

    # 关键修复：只有进行中才显示比赛中
    if match_status(e) == "live":
        return "比赛中\n" + line

    return line


# =========================
# 场馆
# =========================
def location(e):
    venue = e.get("strVenue") or ""
    city = CITIES.get(e.get("strCity"), e.get("strCity") or "")
    country = HOST_COUNTRIES.get(e.get("strCountry"), e.get("strCountry") or "")
    return f"{country} · {city} · {venue}"


# =========================
# 时间
# =========================
def parse_time(e):
    if not e.get("dateEvent"):
        return None

    t = (e.get("strTime") or "00:00:00")[:8]
    dt = datetime.strptime(f"{e['dateEvent']} {t}", "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


# =========================
# API（修复：完整赛程）
# =========================
def fetch_all():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

    endpoints = [
        f"/eventsseason.php?id={LEAGUE_ID}&s={SEASON}",
        f"/eventsnextleague.php?id={LEAGUE_ID}",
        f"/eventspastleague.php?id={LEAGUE_ID}",
    ]

    all_events = []

    for ep in endpoints:
        r = requests.get(url + ep)
        data = r.json()

        if data.get("events"):
            all_events += data["events"]

    # 去重
    seen = set()
    result = []

    for e in all_events:
        eid = e.get("idEvent")
        if eid and eid not in seen:
            seen.add(eid)
            result.append(e)

    return result


# =========================
# ICS
# =========================
def build(events):
    cal = Calendar()

    for e in events:
        start = parse_time(e)
        if not start:
            continue

        ev = Event()
        ev.name = title(e)
        ev.begin = start
        ev.end = start + timedelta(hours=2)
        ev.location = location(e)

        if e.get("idEvent"):
            ev.uid = f"wc2026-{e['idEvent']}"

        cal.events.add(ev)

    return cal


# =========================
# main
# =========================
def main():
    events = fetch_all()
    print("TOTAL:", len(events))

    cal = build(events)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)


if __name__ == "__main__":
    main()
