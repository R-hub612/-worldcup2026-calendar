import requests
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone

API_KEY = "123"
LEAGUE_ID = "4429"
SEASON = "2026"
ICS_FILE = "worldcup2026_schedule.ics"

# =========================
# 国家映射
# =========================
COUNTRIES = {
    "Mexico": ("墨西哥", "MX"),
    "South Africa": ("南非", "ZA"),
    "South Korea": ("韩国", "KR"),
    "Korea Republic": ("韩国", "KR"),
    "Czech Republic": ("捷克", "CZ"),
    "Czechia": ("捷克", "CZ"),
    "Canada": ("加拿大", "CA"),
    "United States": ("美国", "US"),
    "USA": ("美国", "US"),
    "Spain": ("西班牙", "ES"),
    "Paraguay": ("巴拉圭", "PY"),
    "Switzerland": ("瑞士", "CH"),
    "Brazil": ("巴西", "BR"),
    "Morocco": ("摩洛哥", "MA"),
    "Haiti": ("海地", "HT"),
    "Scotland": ("苏格兰", "GB"),
    "Australia": ("澳大利亚", "AU"),
    "Turkey": ("土耳其", "TR"),
    "Germany": ("德国", "DE"),
    "Netherlands": ("荷兰", "NL"),
    "Japan": ("日本", "JP"),
    "Ivory Coast": ("科特迪瓦", "CI"),
    "Ecuador": ("厄瓜多尔", "EC"),
    "Portugal": ("葡萄牙", "PT"),
    "France": ("法国", "FR"),
    "Argentina": ("阿根廷", "AR"),
}

# =========================
# 城市
# =========================
CITIES = {
    "Los Angeles": "洛杉矶",
    "Inglewood": "洛杉矶",
    "New York": "纽约",
    "Dallas": "达拉斯",
    "Houston": "休斯敦",
    "Miami": "迈阿密",
    "Atlanta": "亚特兰大",
    "Seattle": "西雅图",
    "San Francisco": "旧金山",
    "Santa Clara": "旧金山",
}

HOST_COUNTRIES = {
    "United States": "美国",
    "USA": "美国",
    "Canada": "加拿大",
    "Mexico": "墨西哥",
}

# =========================
# emoji
# =========================
def emoji(code):
    if not code:
        return ""
    return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)

# =========================
# 队名
# =========================
def team_cn(name):
    if not name:
        return "待定"
    cn, code = COUNTRIES.get(name, (name, ""))
    return f"{emoji(code)} {cn}".strip()

# =========================
# 组别（修复版）
# =========================
def stage_text(event):
    group = event.get("strGroup")
    stage = event.get("strStage") or event.get("strLeagueRound") or event.get("strRound")

    text = str(group or stage or "").strip()

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

    return mapping.get(text, text)

# =========================
# 比分
# =========================
def score(event):
    hs = event.get("intHomeScore")
    aw = event.get("intAwayScore")
    if hs is None or aw is None:
        return None
    return f"{hs}-{aw}"

# =========================
# 比赛中（最终修复）
# =========================
def is_live(event):
    status = (event.get("strStatus") or "").lower()

    return (
        "live" in status
        or "in progress" in status
        or "1st half" in status
        or "2nd half" in status
        or event.get("intHomeScore") is not None
    )

# =========================
# 标题
# =========================
def title(event):
    home = team_cn(event.get("strHomeTeam"))
    away = team_cn(event.get("strAwayTeam"))

    s = score(event)
    stage = stage_text(event)

    if s:
        line = f"{home} {s} {away}"
    else:
        line = f"{home} vs {away}"

    if stage:
        line += f"｜{stage}"

    if is_live(event):
        return f"比赛中\n{line}"

    return line

# =========================
# 场馆
# =========================
def location(event):
    venue = event.get("strVenue") or ""
    city = CITIES.get(event.get("strCity"), event.get("strCity") or "")
    country = HOST_COUNTRIES.get(event.get("strCountry"), event.get("strCountry") or "")

    return f"{country}{city} · {venue}".strip()

# =========================
# 时间
# =========================
def parse_time(event):
    if not event.get("dateEvent"):
        return None

    t = event.get("strTime") or "00:00:00"
    t = t.replace("Z", "")[:8]

    dt = datetime.strptime(f"{event['dateEvent']} {t}", "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)

# =========================
# API（最终修复）
# =========================
def fetch_matches():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsseason.php"
    r = requests.get(url, params={"id": LEAGUE_ID, "s": SEASON})

    data = r.json().get("events") or []

    # 防止空/脏数据
    return [m for m in data if m.get("dateEvent")]

# =========================
# ICS生成
# =========================
def create_calendar(matches):
    cal = Calendar()

    for m in matches:
        start = parse_time(m)
        if not start:
            continue

        e = Event()
        e.name = title(m)
        e.begin = start
        e.end = start + timedelta(hours=2)
        e.location = location(m)
        e.description = location(m)

        if m.get("idEvent"):
            e.uid = f"worldcup2026-{m['idEvent']}"

        cal.events.add(e)

    return cal

# =========================
# 主函数
# =========================
def main():
    matches = fetch_matches()
    print("TOTAL:", len(matches))

    cal = create_calendar(matches)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    main()
