import os
import requests
from ics import Calendar, Event
from datetime import datetime, timedelta

API_KEY = os.environ["API_KEY"]

BASE_URL = "https://v3.football.api-sports.io/fixtures"

# ======================
# 48队（稳定映射）
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
    "South Korea": ("韩国", "KR"),
    "Korea Republic": ("韩国", "KR"),
    "Canada": ("加拿大", "CA"),
    "Morocco": ("摩洛哥", "MA"),
    "Qatar": ("卡塔尔", "QA"),
    "Switzerland": ("瑞士", "CH"),
    "Netherlands": ("荷兰", "NL"),
    "Belgium": ("比利时", "BE"),
    "Uruguay": ("乌拉圭", "UY"),
    "Croatia": ("克罗地亚", "HR"),
    "Ecuador": ("厄瓜多尔", "EC"),
    "USA": ("美国", "US"),
    "Saudi Arabia": ("沙特阿拉伯", "SA"),
    "Australia": ("澳大利亚", "AU"),
    "Tunisia": ("突尼斯", "TN"),
    "Poland": ("波兰", "PL"),
    "Serbia": ("塞尔维亚", "RS"),
    "Ghana": ("加纳", "GH"),
    "Cameroon": ("喀麦隆", "CM"),
    "Senegal": ("塞内加尔", "SN"),
    "Iran": ("伊朗", "IR"),
}

ALIASES = {
    "Ivory Coast": "Côte d'Ivoire",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "South Korea": "Korea Republic",
    "USA": "United States",
}

def emoji(code):
    if not code:
        return ""
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)

def normalize_team(name):
    return ALIASES.get(name, name)

def team(name):
    name = normalize_team(name)
    cn, code = COUNTRIES.get(name, (name, ""))
    return f"{emoji(code)} {cn}"

def fetch():
    headers = {"x-apisports-key": API_KEY}

    r = requests.get(BASE_URL, headers=headers, params={"season": 2026})

    data = r.json().get("response", [])

    return data

def parse_time(item):
    return datetime.fromisoformat(
        item["fixture"]["date"].replace("Z", "+00:00")
    )

def status(item):
    return item["fixture"]["status"]["short"]

def build(data):
    cal = Calendar()

    for item in data:
        if not item.get("teams"):
            continue

        home = team(item["teams"]["home"]["name"])
        away = team(item["teams"]["away"]["name"])

        st = status(item)
        goals = item.get("goals", {})

        if st in ["FT"]:
            title = f"{home} {goals.get('home','')} - {goals.get('away','')} {away}"
        elif st in ["1H", "2H", "LIVE", "HT"]:
            title = f"🔴 比赛中 {home} vs {away}"
        else:
            title = f"{home} vs {away}"

        ev = Event()
        ev.name = title
        ev.begin = parse_time(item)
        ev.end = ev.begin + timedelta(hours=2)
        ev.uid = f"wc2026-{item['fixture']['id']}"

        cal.events.add(ev)

    return cal

def main():
    data = fetch()
    cal = build(data)

    with open("worldcup2026.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    main()
