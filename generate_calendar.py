import requests
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone

API_KEY = "123"
LEAGUE_ID = "4429"
SEASON = "2026"
ICS_FILE = "worldcup2026_schedule.ics"

# ======================
# 国家
# ======================
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
}

# ======================
# 城市
# ======================
CITIES = {
    "Los Angeles": "洛杉矶",
    "Inglewood": "洛杉矶",
    "New York": "纽约",
    "Dallas": "达拉斯",
    "Miami": "迈阿密",
    "Seattle": "西雅图",
    "San Francisco": "旧金山",
}

HOST_COUNTRIES = {
    "United States": "美国",
    "USA": "美国",
    "Mexico": "墨西哥",
    "Canada": "加拿大",
}

# ======================
# emoji
# ======================
def emoji(code):
    if not code:
        return ""
    return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)

# ======================
# 队伍
# ======================
def team(name):
    if not name:
        return "待定"
    cn, code = COUNTRIES.get(name, (name, ""))
    return f"{emoji(code)} {cn}"

# ======================
# 组别
# ======================
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
    return mapping.get(g, g)

# ======================
# 比分
# ======================
def score(e):
    hs = e.get("intHomeScore")
    aw = e.get("intAwayScore")
    if hs is None or aw is None:
        return None
    return f"{hs}-{aw}"

# ======================
# 🔥 最终比赛状态（重写）
# ======================
def is_finished(e):
    return (e.get("strStatus") or "").lower() in ["ft", "finished", "match finished"]

def is_live(e):
    status = (e.get("strStatus") or "").lower()
    return (
        not is_finished(e)
        and (
            "live" in status
            or "in progress" in status
            or "1st half" in status
            or "2nd half" in status
            or "halftime" in status
            or e.get("intHomeScore") is not None
        )
    )

# ======================
# 标题（最终稳定版）
# ======================
def title(e):
    home = team(e.get("strHomeTeam"))
    away = team(e.get("strAwayTeam"))

    s = score(e)
    st = stage(e)

    line = f"{home} vs {away}"

    if s:
        line = f"{home} {s} {away}"

    if st:
        line += f" ｜{st}"

    if is_live(e):
        return "比赛中\n" + line

    return line

# ======================
# 场馆
# ======================
def location(e):
    venue = e.get("strVenue") or ""
    city = CITIES.get(e.get("strCity"), e.get("strCity") or "")
    country = HOST_COUNTRIES.get(e.get("strCountry"), e.get("strCountry") or "")
    return f"{country} · {city} · {venue}".strip()

# ======================
# 时间
# ======================
def parse_time(e):
    if not e.get("dateEvent"):
        return None
    t = (e.get("strTime") or "00:00:00")[:8]
    dt = datetime.strptime(f"{e['dateEvent']} {t}", "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)

# ======================
# API（必须用完整赛程）
# ======================
def fetch():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsseason.php"
    r = requests.get(url, params={"id": LEAGUE_ID, "s": SEASON})
    data = r.json().get("events") or []

    # 不再错误过滤
    return data

# ======================
# ICS生成
# ======================
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

# ======================
# main
# ======================
def main():
    events = fetch()
    print("TOTAL EVENTS:", len(events))

    cal = build(events)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    main()
