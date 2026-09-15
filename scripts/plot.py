#!/usr/bin/env python3
"""Plot weather history from data/meteo.csv into plots/meteo_history.png.

Per-source series:
- sensor: EMOS-E6016 RTL-SDR readings (grey) + daily mean (blue)
- era5:  Open-Meteo ERA5 reanalysis hourly (orange, fills the gaps)
- chmi:  CHMI Praha-Karlov daily (red markers, fills the gaps)
"""

import csv
import math
import os
from collections import defaultdict
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "meteo.csv")
OUT = os.path.join(BASE, "plots", "meteo_history.png")

VARS = ["temperature_C", "humidity", "wind_avg_m_s", "wind_dir_deg"]
PANELS = [
    ("Temperature", "°C"),
    ("Humidity", "%"),
    ("Wind speed", "m/s"),
    ("Wind direction", "deg"),
]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def load():
    by_source = {}
    for src in ("sensor", "era5", "chmi"):
        by_source[src] = {v: ([], []) for v in VARS}
    with open(CSV) as fh:
        for row in csv.DictReader(fh):
            src = row.get("source", "sensor")
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if src not in by_source:
                continue
            for v in VARS:
                by_source[src][v][0].append(t)
                by_source[src][v][1].append(_num(row.get(v, "")))
    return by_source


def _daily_mean(times, series):
    if not times:
        return [], []
    by_day = defaultdict(list)
    for t, v in zip(times, series):
        if not math.isnan(v):
            by_day[t.date()].append(v)
    days = sorted(by_day)
    return [datetime.combine(d, datetime.min.time()) for d in days], [
        sum(by_day[d]) / len(by_day[d]) for d in days
    ]


def main():
    data = load()
    n = sum(len(data[src]["temperature_C"][0]) for src in data)
    print("{} points loaded from {}".format(n, CSV))

    fig, axes = plt.subplots(4, 1, figsize=(15, 14), sharex=True)
    fig.suptitle(
        "Meteostation EMOS-E6016 / Observator Soběslavská, Praha 3\n"
        "EMOS sensor  (2023-06-25 → 2026-09-15) · ERA5 reanalysis · CHMI Praha-Karlov (daily)",
        fontsize=13,
    )

    for i, (title, unit) in enumerate(PANELS):
        ax = axes[i]
        var = VARS[i]

        st, sv = data["sensor"][var]
        ax.plot(st, sv, color="0.65", linewidth=0.4, alpha=0.6, label="_nolabel_")
        dts, means = _daily_mean(st, sv)
        ax.plot(dts, means, color="#0b5394", linewidth=1.4, label="EMOS daily mean")

        if var == "wind_dir_deg":
            et, ev = data["era5"][var]
            ax.plot(
                et, ev, color="#e67e22", linewidth=0.7, alpha=0.9, label="ERA5 hourly"
            )
        else:
            et, ev = data["era5"][var]
            ax.plot(et, ev, color="#e67e22", linewidth=1.0, label="ERA5 hourly")

        ct, cv = data["chmi"][var]
        if var == "wind_dir_deg":
            # keep only valid angles, CHMI daily has no wind direction
            pairs = [(t, v) for t, v in zip(ct, cv) if not math.isnan(v)]
            if pairs:
                ct, cv = zip(*pairs)
            else:
                ct, cv = [], []
        ax.plot(
            ct,
            cv,
            color="#c0392b",
            marker="o",
            markersize=2,
            linestyle="None",
            label="CHMI Karlov daily",
        )

        ax.set_ylabel(unit, fontsize=10)
        ax.set_title(title, fontsize=11, loc="left")
        ax.grid(True, alpha=0.3)

    axes[3].xaxis.set_major_locator(mdates.MonthLocator())
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()

    axes[0].legend(loc="upper left", fontsize=9, ncol=3)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=140)
    print("saved {}".format(OUT))


if __name__ == "__main__":
    main()
