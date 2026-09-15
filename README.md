# Meteodata — Observator Soběslavská, Praha 3

Historical weather data from an EMOS-E6016 weather station, received via
RTL-SDR / rtl_433 and logged by a Raspberry Pi at home.

Data spans **2023-06-25 → 2026-09-15** (178,996 deduplicated records).
Source files: `data/raw/*.json` (rtl_433 JSON-lines). Merged/canonical CSV:
`data/meteo.csv`.

## Data

Columns: `time, id, battery_ok, temperature_C, humidity, wind_avg_m_s,
wind_dir_deg`.

The station id changes over time (108/212 → 87 → 75 → 131), likely battery
swaps in the outdoor unit. There are data gaps **2023-09-10 → 2025-11-06**
(~2 years, logging outage) and **2025-12-01 → 2026-05-23**. Raw files overlap
on 2026-07-30; `scripts/merge.py` deduplicates by `(time, id)`.

`battery_ok: 0` in the Nov 2025 batch indicates that battery was low.

## Plots

`plots/meteo_history.png` — temperature, humidity, wind speed and wind
direction time series, with daily-mean overlay:

![meteo history](plots/meteo_history.png)

## Reproducing

```sh
python3 scripts/merge.py   # rebuild data/meteo.csv from data/raw/
python3 scripts/plot.py    # regenerate plots/meteo_history.png
```

Requires Python 3 + matplotlib. No pandas needed.

## Source / hardware

- Upstream parser: `rtl_sdr-weather_data_parser` (GPLv3)
- Logged on a Raspberry Pi, retrieved via:
  ```
  ssh pi 'sudo cat /root/rtl_sdr-weather_data_parser/<file>.json'
  ```
  (`backup2.json`, `weather_data_all.json` in `/var/log`, `backup.json`,
  `graph.json` — the live file)
- The 2023 epoch (`2023_graph.json`) was recovered from the previous backup
  repo `K0F/meteodata` (2023-06-25 → 2023-09-10, ids 108/212).