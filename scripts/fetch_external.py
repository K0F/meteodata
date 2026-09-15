#!/usr/bin/env python3
"""Fetch gap-filling weather data for the Soběslavská observatory location.

Two sources, both CC BY 4.0:

- CHMI (Czech Hydrometeorological Institute) - daily data from the nearest
  professional station "Praha, Karlov" (WSI 0-20000-0-11519, ~2.1 km away).
  Covers the gaps at daily resolution.
- Open-Meteo ERA5 reanalysis (archive-api.open-meteo.com, no key needed) at
  the observatory coordinates (50.0877, 14.4428) - hourly resolution.

Writes:
  data/raw/chmi_karlov_daily.csv
  data/raw/era5_gaps.csv

Both in the same schema as data/meteo.csv plus a `source` column.
"""

import csv
import json
import os
import sys
from datetime import date, datetime, timedelta

import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "data", "raw")
CHMI_OUT = os.path.join(RAW_DIR, "chmi_karlov_daily.csv")
ERA5_OUT = os.path.join(RAW_DIR, "era5_gaps.csv")

WSI = "0-20000-0-11519"
CHMI_HIST = (
    "https://opendata.chmi.cz/meteorology/climate/historical/data/daily/dly-{wsi}.json"
)
CHMI_RECENT = (
    "https://opendata.chmi.cz/meteorology/climate/recent/"
    "data/daily/{mm}/dly-{wsi}-{yyyymm}.json"
)
ERA5_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=50.0877&longitude=14.4428"
    "&hourly=temperature_2m,relative_humidity_2m,"
    "wind_speed_10m,wind_direction_10m"
    "&wind_speed_unit=ms&timezone=Europe/Prague"
    "&start_date={start}&end_date={end}"
)

FIELDS = [
    "time",
    "source",
    "id",
    "battery_ok",
    "temperature_C",
    "humidity",
    "wind_avg_m_s",
    "wind_dir_deg",
]

GAPS = [
    (date(2023, 9, 10), date(2025, 11, 6)),
    (date(2025, 12, 1), date(2026, 5, 23)),
    (date(2026, 9, 7), date(2026, 9, 10)),
]


def _fetch(url):
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read()


def _months_for_gaps():
    months = set()
    for start, end in GAPS:
        d = start
        while d <= end:
            months.add((d.year, d.month))
            d += timedelta(days=1)
    return sorted(months)


def _chmi_url_groups():
    """Yield lists of candidate URLs (subfolder + root fallback)."""
    yield [CHMI_HIST.format(wsi=WSI)]
    for y, m in _months_for_gaps():
        if date(y, m, 1) < date(2026, 1, 1):
            continue  # already inside the historical file
        key = "{}{:02d}".format(y, m)
        mm = "{:02d}".format(m)
        yield [
            CHMI_RECENT.format(wsi=WSI, mm=mm, yyyymm=key),
            CHMI_RECENT.format(wsi=WSI, mm="", yyyymm=key).replace(
                "/daily//", "/daily/"
            ),
        ]


def _fetch_any(urls):
    """Fetch the first URL that returns HTTP 200."""
    for url in urls:
        try:
            return _fetch(url), url
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    raise RuntimeError("all URL candidates failed: {}".format(urls))


def _chmi_daily_rows():
    """Yield (time, temp, humidity, wind) daily CHMI rows for gap windows."""
    by_day = {}
    # (time, element) -> value for VTYPE==AVG rows inside the gaps
    for group in _chmi_url_groups():
        data, used = _fetch_any(group)
        print("  fetched {}".format(used), file=sys.stderr)
        data = json.loads(data)
        for row in data["data"]["data"]["values"]:
            _, elem, vtype, dt, val, _, _ = row
            if vtype != "AVG" or elem not in ("T", "H", "F"):
                continue
            day = datetime.strptime(dt[:10], "%Y-%m-%d").date()
            if not any(s <= day <= e for s, e in GAPS):
                continue
            try:
                fval = float(val)
            except (TypeError, ValueError):
                continue
            by_day.setdefault(day, {})[elem] = fval
    for day in sorted(by_day):
        r = by_day[day]
        if "T" not in r or "H" not in r or "F" not in r:
            continue
        yield day.strftime("%Y-%m-%d 00:00:00"), r["T"], r["H"], r["F"]


def _write_chmi():
    rows = 0
    with open(CHMI_OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for time, temp, hum, wind in _chmi_daily_rows():
            w.writerow(
                {
                    "time": time,
                    "source": "chmi",
                    "id": "11519",
                    "battery_ok": "",
                    "temperature_C": temp,
                    "humidity": hum,
                    "wind_avg_m_s": wind,
                    "wind_dir_deg": "",
                }
            )
            rows += 1
    print("chmi: {} daily rows -> {}".format(rows, CHMI_OUT), file=sys.stderr)


def _write_era5():
    rows = 0
    with open(ERA5_OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for start, end in GAPS:
            url = ERA5_URL.format(start=start.isoformat(), end=end.isoformat())
            print("  fetching {}".format(url), file=sys.stderr)
            data = json.loads(_fetch(url))
            h = data["hourly"]
            for t, temp, hum, wind, direction in zip(
                h["time"],
                h["temperature_2m"],
                h["relative_humidity_2m"],
                h["wind_speed_10m"],
                h["wind_direction_10m"],
            ):
                w.writerow(
                    {
                        "time": t.replace("T", " ") + ":00",
                        "source": "era5",
                        "id": "ERA5",
                        "battery_ok": "",
                        "temperature_C": temp,
                        "humidity": hum,
                        "wind_avg_m_s": wind,
                        "wind_dir_deg": direction,
                    }
                )
                rows += 1
    print("era5: {} hourly rows -> {}".format(rows, ERA5_OUT), file=sys.stderr)


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    _write_chmi()
    _write_era5()


if __name__ == "__main__":
    main()
