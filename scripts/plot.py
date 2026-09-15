#!/usr/bin/env python3
"""Plot weather history from data/meteo.csv into plots/meteo_history.png."""

import csv
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


def load():
    times, temp, hum, wind, direction = [], [], [], [], []
    with open(CSV) as fh:
        for row in csv.DictReader(fh):
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            times.append(t)
            temp.append(_num(row["temperature_C"]))
            hum.append(_num(row["humidity"]))
            wind.append(_num(row["wind_avg_m_s"]))
            direction.append(_num(row["wind_dir_deg"]))
    return times, temp, hum, wind, direction


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def _daily_mean(times, series):
    by_day = defaultdict(list)
    for t, v in zip(times, series):
        import math

        if not math.isnan(v):
            by_day[t.date()].append(v)
    days = sorted(by_day)
    return [datetime.combine(d, datetime.min.time()) for d in days], [
        sum(by_day[d]) / len(by_day[d]) for d in days
    ]


def main():
    times, temp, hum, wind, direction = load()
    print("{} points loaded from {}".format(len(times), CSV))

    fig, axes = plt.subplots(4, 1, figsize=(14, 14), sharex=True)
    fig.suptitle(
        "Meteostation EMOS-E6016 / Observator Soběslavská, Praha 3", fontsize=14
    )

    panels = [
        (axes[0], temp, "Temperature (°C)", "°C"),
        (axes[1], hum, "Humidity (%)", "%"),
        (axes[2], wind, "Wind speed (m/s)", "m/s"),
        (axes[3], direction, "Wind direction (deg)", "deg"),
    ]

    for ax, series, title, _unit in panels:
        ax.plot(times, series, color="0.65", linewidth=0.4, alpha=0.6)
        dts, means = _daily_mean(times, series)
        ax.plot(dts, means, color="#0b5394", linewidth=1.4)
        ax.set_ylabel(_unit, fontsize=10)
        ax.set_title(title, fontsize=11, loc="left")
        ax.grid(True, alpha=0.3)

    axes[3].xaxis.set_major_locator(mdates.MonthLocator())
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=140)
    print("saved {}".format(OUT))


if __name__ == "__main__":
    main()
