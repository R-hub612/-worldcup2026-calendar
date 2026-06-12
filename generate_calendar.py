import requests
from ics import Calendar, Event
from datetime import datetime, timedelta

TOKEN = "a5507e9b27da40b9a0f49744f268d163"

ICS_FILE = "worldcup2026_schedule.ics"


def fetch_matches():

    headers = {
        "X-Auth-Token": TOKEN
    }

    start_date = datetime(2026, 6, 12)
    end_date = datetime(2026, 7, 20)

    all_matches = []

    current = start_date

    while current < end_date:

        chunk_end = min(
            current + timedelta(days=9),
            end_date
        )

        params = {
            "competitions": "WC",
            "dateFrom": current.strftime("%Y-%m-%d"),
            "dateTo": chunk_end.strftime("%Y-%m-%d")
        }

        url = "https://api.football-data.org/v4/matches"

        r = requests.get(
            url,
            headers=headers,
            params=params
        )

        print(
            current.strftime("%Y-%m-%d"),
            chunk_end.strftime("%Y-%m-%d"),
            r.status_code
        )

        print(r.text)

        r.raise_for_status()

        data = r.json()

        if "matches" in data:
            all_matches.extend(data["matches"])

        current = chunk_end + timedelta(days=1)

    return all_matches


def create_calendar(matches):

    cal = Calendar()

    for m in matches:

        e = Event()

        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]

        utc = datetime.fromisoformat(
            m["utcDate"].replace("Z", "+00:00")
        )

        beijing_time = utc + timedelta(hours=8)

        e.name = f"{home} vs {away}"

        e.begin = beijing_time

        cal.events.add(e)

    return cal


def main():

    matches = fetch_matches()

    print("TOTAL MATCHES:", len(matches))

    cal = create_calendar(matches)

    with open(
        ICS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.writelines(cal)


if __name__ == "__main__":
    main()
