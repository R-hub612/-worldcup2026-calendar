import requests
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone

API_KEY = "123"
LEAGUE_ID = "4429"
SEASON = "2026"
ICS_FILE = "worldcup2026_schedule.ics"

# =========================
# 国家映射（补全版）
# =========================
COUNTRIES = {
    "Mexico": ("墨西哥", "MX"),
    "South Africa": ("南非", "ZA"),
    "South Korea": ("韩国", "KR"),
    "Korea Republic": ("韩国", "KR"),
    "Czech Republic": ("捷克", "CZ"),
    "Czechia": ("捷克", "CZ"),
    "Canada": ("加拿大", "CA"),
    "Bosnia-Herzegovina": ("波黑", "BA"),
    "Bosnia and Herzegovina": ("波黑", "BA"),
    "United States": ("美国", "US"),
    "USA": ("美国", "US"),
    "Spain": ("西班牙", "ES"),
    "Espana": ("西班牙", "ES"),
    "Paraguay": ("巴拉圭", "PY"),
    "Qatar": ("卡塔尔", "QA"),
    "Switzerland": ("瑞士", "CH"),
    "Brazil": ("巴西", "BR"),
    "Morocco": ("摩洛哥", "MA"),
    "Haiti": ("海地", "HT"),
    "Scotland": ("苏格兰", "GB"),
    "Australia": ("澳大利亚", "AU"),
    "Turkey": ("土耳其", "TR"),
    "Germany": ("德国", "DE"),
    "Curaçao": ("库拉索", "CW"),
    "Curacao": ("库拉索", "CW"),
    "Netherlands": ("荷兰", "NL"),
    "Japan": ("日本", "JP"),
    "Ivory Coast": ("科特迪瓦", "CI"),
    "Côte d’Ivoire": ("科特迪瓦", "CI"),
    "Ecuador": ("厄瓜多尔", "EC"),
}

# =========================
# 城市映射
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
    if not code or len(code) < 2:
        return ""
    code = code[:2].upper()
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)

# =========================
# 队名中文 + 国旗
# =========================
def team_cn(name):
    if not name:
        return "待定"
    cn, code = COUNTRIES.get(name, (name, ""))
    flag = emoji(code)
    return f"{flag} {cn}".strip()

# =========================
# 组别 / 阶段（修复版）
# =========================
def stage_text(event):
    group = event.get("strGroup") or event.get("strGroupName")
    stage = (
        event.get("strStage")
        or event.get("strLeagueRound")
        or event.get("strRound")
        or event.get("intRound")
    )

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
    if hs in [None, ""] or aw in [None, ""]:
        return None
    return f"{hs}-{aw}"

# =========================
# 比赛中判断（修复版）
# =========================
def is_live(event):
    status = (event.get("strStatus") or "").lower()
    return (
        "live" in status
        or "in progress" in status
        or event.get("strProgress") not in [None, ""]
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
# 场地
# =========================
def location(event):
    venue = event.get("strVenue") or ""
    city_raw = event.get("strCity") or ""
    country_raw = event.get("strCountry") or ""

    city_cn = CITIES.get(city_raw, city_raw)
    country_cn = HOST_COUNTRIES.get(country_raw, country_raw)

    prefix = f"{country_cn}{city_cn}".strip()

    if prefix and venue:
        return f"{prefix} · {venue}"
    if venue:
        return venue
    return prefix

# =========================
# 时间
# =========================
def parse_time(event):
    date_str = event.get("dateEvent")
    time_str = event.get("strTime") or "00:00:00"

    if not date_str:
        return None

    time_str = time_str.replace("Z", "").replace("+00:00", "")[:8]
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)

# =========================
# API（修复：不截断赛程）
# =========================
def fetch_matches():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php"
    params = {"id": LEAGUE_ID}

    r = requests.get(url, params=params)
    print("STATUS:", r.status_code)
    r.raise_for_status()

    return r.json().get("events") or []

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
    print("TOTAL MATCHES:", len(matches))

    cal = create_calendar(matches)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    main()
