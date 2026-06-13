import requests
from ics import Calendar, Event
from datetime import datetime, timedelta, timezone

API_KEY = "123"
LEAGUE_ID = "4429"
SEASON = "2026"
ICS_FILE = "worldcup2026_schedule.ics"


TEAM_DB = {
    "mexico": ("墨西哥", "🇲🇽"),
    "south africa": ("南非", "🇿🇦"),
    "korea republic": ("韩国", "🇰🇷"),
    "south korea": ("韩国", "🇰🇷"),
    "czech republic": ("捷克", "🇨🇿"),
    "czechia": ("捷克", "🇨🇿"),
    "canada": ("加拿大", "🇨🇦"),
    "bosnia and herzegovina": ("波黑", "🇧🇦"),
    "qatar": ("卡塔尔", "🇶🇦"),
    "switzerland": ("瑞士", "🇨🇭"),
    "brazil": ("巴西", "🇧🇷"),
    "morocco": ("摩洛哥", "🇲🇦"),
    "haiti": ("海地", "🇭🇹"),
    "scotland": ("苏格兰", "🏴"),
    "united states": ("美国", "🇺🇸"),
    "usa": ("美国", "🇺🇸"),
    "paraguay": ("巴拉圭", "🇵🇾"),
    "australia": ("澳大利亚", "🇦🇺"),
    "turkey": ("土耳其", "🇹🇷"),
    "germany": ("德国", "🇩🇪"),
    "curacao": ("库拉索", "🇨🇼"),
    "cote d'ivoire": ("科特迪瓦", "🇨🇮"),
    "côte d’ivoire": ("科特迪瓦", "🇨🇮"),
    "ecuador": ("厄瓜多尔", "🇪🇨"),
    "netherlands": ("荷兰", "🇳🇱"),
    "japan": ("日本", "🇯🇵"),
    "sweden": ("瑞典", "🇸🇪"),
    "tunisia": ("突尼斯", "🇹🇳"),
    "belgium": ("比利时", "🇧🇪"),
    "egypt": ("埃及", "🇪🇬"),
    "iran": ("伊朗", "🇮🇷"),
    "new zealand": ("新西兰", "🇳🇿"),
    "spain": ("西班牙", "🇪🇸"),
    "cape verde": ("佛得角", "🇨🇻"),
    "saudi arabia": ("沙特阿拉伯", "🇸🇦"),
    "uruguay": ("乌拉圭", "🇺🇾"),
    "france": ("法国", "🇫🇷"),
    "senegal": ("塞内加尔", "🇸🇳"),
    "iraq": ("伊拉克", "🇮🇶"),
    "norway": ("挪威", "🇳🇴"),
    "argentina": ("阿根廷", "🇦🇷"),
    "algeria": ("阿尔及利亚", "🇩🇿"),
    "austria": ("奥地利", "🇦🇹"),
    "jordan": ("约旦", "🇯🇴"),
    "portugal": ("葡萄牙", "🇵🇹"),
    "dr congo": ("刚果（金）", "🇨🇩"),
    "uzbekistan": ("乌兹别克斯坦", "🇺🇿"),
    "colombia": ("哥伦比亚", "🇨🇴"),
    "england": ("英格兰", "🏴"),
    "croatia": ("克罗地亚", "🇭🇷"),
    "ghana": ("加纳", "🇬🇭"),
    "panama": ("巴拿马", "🇵🇦"),
}


# 🔥 仅补这两个 alias（最终补丁）
ALIAS = {
    "ivory coast": "cote d'ivoire",
    "cote d'ivoire": "cote d'ivoire",
    "côte d’ivoire": "cote d'ivoire",

    "curacao": "curacao",
    "curaçao": "curacao",
}


def norm(n):
    return (n or "").strip().lower()


def resolve_team(name):
    n = norm(name)

    # alias层
    n = ALIAS.get(n, n)

    # 标准库
    if n in TEAM_DB:
        cn, flag = TEAM_DB[n]
        return f"{flag} {cn}"

    return name


def score(e):
    h = e.get("intHomeScore")
    a = e.get("intAwayScore")
    if h is None or a is None:
        return None
    return f"{h}-{a}"


def status(e):
    s = (e.get("strStatus") or "").upper()
    if s in ["1H", "2H", "LIVE"]:
        return "LIVE"
    if s == "FT":
        return "FT"
    return "NS"


def title(e):
    home = resolve_team(e.get("strHomeTeam"))
    away = resolve_team(e.get("strAwayTeam"))

    sc = score(e)

    base = f"{home} vs {away}" if not sc else f"{home} {sc} {away}"

    if status(e) == "LIVE":
        return "▶️ 比赛中\n" + base

    return base


def parse_time(e):
    if not e.get("dateEvent"):
        return None
    t = (e.get("strTime") or "00:00:00")[:8]
    dt = datetime.strptime(f"{e['dateEvent']} {t}", "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


def fetch():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsseason.php"
    r = requests.get(url, params={"id": LEAGUE_ID, "s": SEASON})
    return r.json().get("events") or []


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

        ev.location = f"{e.get('strCountry','')} · {e.get('strCity','')} · {e.get('strVenue','')}"

        if e.get("idEvent"):
            ev.uid = f"wc2026-{e['idEvent']}"

        cal.events.add(ev)

    return cal


def main():
    events = fetch()
    cal = build(events)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)


if __name__ == "__main__":
    main()
