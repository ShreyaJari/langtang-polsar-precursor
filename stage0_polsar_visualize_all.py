#!/usr/bin/env python3
"""
stage0_polsar_visualize_all.py

Generates all three precursor-finding visualizations from the single
stage0_polsar_timeseries.csv (produced by stage0_polsar.py):

1. Hero chart -- annotated overlay of all three zones, full context,
   event dates and precursor minima called out.
2. Small multiples -- one panel per zone, shared y-axis, makes the
   dip's isolation to the detachment zone visually unmistakable.
3. Year-over-year overlay -- detachment zone's 2025 and 2026 cycles
   on a shared calendar axis, directly visualizing the replication.

Requirements
------------
    conda activate nepal-flood
    pip install pandas matplotlib

Usage
-----
    python3 stage0_polsar_visualize_all.py
"""

from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CSV_PATH = Path.home() / "_GeoAI_Notebook" / "langtang-polsar-precursor" / "stage0_polsar_output" / "stage0_polsar_timeseries.csv"
OUTPUT_DIR = Path.home() / "_GeoAI_Notebook" / "langtang-polsar-precursor" / "stage0_polsar_output"

# -----------------------------------------------------------------------
# Shared constants
# -----------------------------------------------------------------------

EVENTS = [
    ("2025-07-08", "Jul 8, 2025\nLake outburst flood"),
    ("2026-08-26", "Aug 26, 2026\nGlacier collapse"),
]
MELT_SEASONS = [("2025-04-01", "2025-08-31"), ("2026-04-01", "2026-08-31")]

# Precursor minima -- (date, value, label, annotation offset in points).
# Update these if you re-run stage0_polsar.py and the minima shift.
MINIMA = [
    ("2025-05-10", -13.95, "May 10, 2025\n\u201359 days before outburst", (30, 55)),
    ("2026-05-17", -15.83, "May 17, 2026\n\u2013101 days before collapse", (-10, 70)),
]

CONTROL_COLORS = {"ghenge_liru": "#5b7ea3", "gangchempo": "#6fa287"}
CONTROL_LABELS = {"ghenge_liru": "Ghenge Liru (control, 3km)", "gangchempo": "Gangchempo (control, 15km)"}
DETACHMENT_COLOR = "#c0392b"
EVENT_COLOR = "#8e2828"

COLOR_2025 = "#e0836b"
COLOR_2026 = "#8e2828"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


# -----------------------------------------------------------------------
# 1. Hero chart
# -----------------------------------------------------------------------

def build_hero_chart(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 7.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfb")

    for start, end in MELT_SEASONS:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color="#f4a13c", alpha=0.08, zorder=0)

    for zone in ["ghenge_liru", "gangchempo"]:
        g = df[df["zone"] == zone].sort_values("date")
        ax.plot(g["date"], g["cross_pol_ratio_db"], color=CONTROL_COLORS[zone],
                 label=CONTROL_LABELS[zone], linewidth=1.4, alpha=0.55,
                 marker="o", markersize=3.5)

    g = df[df["zone"] == "detachment"].sort_values("date")
    ax.plot(g["date"], g["cross_pol_ratio_db"], color=DETACHMENT_COLOR, linewidth=2.8,
             marker="o", markersize=5, label="Detachment zone", zorder=5)

    data_min = df["cross_pol_ratio_db"].min()
    data_max = df["cross_pol_ratio_db"].max()
    margin = (data_max - data_min) * 0.15
    ax.set_ylim(data_min - margin, data_max + margin)

    for date_str, label in EVENTS:
        date = pd.Timestamp(date_str)
        ax.axvline(date, color=EVENT_COLOR, linestyle="--", linewidth=1.4, alpha=0.85, zorder=3)
        ax.annotate(label, xy=(date, 1.0), xycoords=("data", "axes fraction"),
                    xytext=(0, 8), textcoords="offset points",
                    fontsize=10.5, fontweight="bold", color=EVENT_COLOR, ha="center", va="bottom")

    for date_str, value, label, offset in MINIMA:
        date = pd.Timestamp(date_str)
        ax.scatter([date], [value], s=200, facecolors="none", edgecolors=EVENT_COLOR,
                   linewidths=2.5, zorder=6)
        ax.annotate(label, xy=(date, value), xytext=offset, textcoords="offset points",
                    fontsize=9.5, ha="center", color=EVENT_COLOR, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=EVENT_COLOR, lw=1.2, alpha=0.7))

    ax.set_ylabel("Cross-pol ratio, VH \u2212 VV (dB)", fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.get_xticklabels(), fontsize=10)
    ax.tick_params(axis="y", labelsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)

    ax.set_title("A Recurring Precursor Signal at the Langtang Lirung Failure Zone",
                 fontsize=17, fontweight="bold", pad=52, loc="left")
    ax.text(0, 1.10,
            "Dual-pol Sentinel-1 cross-pol ratio dips \u2248 2\u20133.5 months before both the "
            "2025 lake outburst and 2026 glacier collapse \u2014 absent at two independent control sites",
            transform=ax.transAxes, fontsize=11.5, color="#555555", ha="left")

    ax.legend(loc="lower right", fontsize=10.5, framealpha=0.95, edgecolor="#cccccc")
    plt.tight_layout(rect=[0, 0, 1, 0.90])

    png_path = OUTPUT_DIR / "langtang_polsar_precursor_finding.png"
    pdf_path = OUTPUT_DIR / "langtang_polsar_precursor_finding.pdf"
    plt.savefig(png_path, dpi=300, facecolor="white")
    plt.savefig(pdf_path, facecolor="white")
    plt.close(fig)
    print(f"Saved {png_path}")
    print(f"Saved {pdf_path}")


# -----------------------------------------------------------------------
# 2. Small multiples
# -----------------------------------------------------------------------

def build_small_multiples(df: pd.DataFrame):
    zone_order = ["detachment", "ghenge_liru", "gangchempo"]
    zone_colors = {"detachment": DETACHMENT_COLOR, **CONTROL_COLORS}
    zone_titles = {
        "detachment": "Detachment zone",
        "ghenge_liru": "Ghenge Liru (control, 3km away)",
        "gangchempo": "Gangchempo (control, 15km away)",
    }
    minima_by_zone = [("detachment", d, v, l) for d, v, l, _ in MINIMA]

    data_min, data_max = df["cross_pol_ratio_db"].min(), df["cross_pol_ratio_db"].max()
    margin = (data_max - data_min) * 0.1
    ylim = (data_min - margin, data_max + margin)

    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
    fig.patch.set_facecolor("white")

    for ax, zone in zip(axes, zone_order):
        ax.set_facecolor("#fbfbfb")
        for start, end in MELT_SEASONS:
            ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color="#f4a13c", alpha=0.08, zorder=0)
        for date_str, _ in EVENTS:
            ax.axvline(pd.Timestamp(date_str), color=EVENT_COLOR, linestyle="--",
                       linewidth=1.2, alpha=0.75, zorder=3)

        g = df[df["zone"] == zone].sort_values("date")
        ax.plot(g["date"], g["cross_pol_ratio_db"], color=zone_colors[zone],
                 linewidth=2.2, marker="o", markersize=4, zorder=5)

        for min_zone, date_str, value, _ in minima_by_zone:
            if min_zone != zone:
                continue
            date = pd.Timestamp(date_str)
            ax.scatter([date], [value], s=170, facecolors="none", edgecolors=EVENT_COLOR,
                       linewidths=2.2, zorder=6)

        ax.set_ylim(*ylim)
        ax.set_ylabel(zone_titles[zone], fontsize=11.5, fontweight="500")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.2, linewidth=0.6)
        ax.tick_params(axis="y", labelsize=9.5)

    for date_str, label in EVENTS:
        axes[0].annotate(label.replace("\n", " \u2014 "), xy=(pd.Timestamp(date_str), 1.0),
                          xycoords=("data", "axes fraction"), xytext=(0, 8),
                          textcoords="offset points", fontsize=9.5, fontweight="bold",
                          color=EVENT_COLOR, ha="center", va="bottom")

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(axes[-1].get_xticklabels(), fontsize=10)

    fig.suptitle("Same signal, same scale, three sites", fontsize=17,
                 fontweight="bold", x=0.09, y=0.985, ha="left")
    fig.text(0.09, 0.955,
             "Cross-pol ratio (VH \u2212 VV, dB) on an identical y-axis across all three panels \u2014 "
             "only the detachment zone shows a deep, isolated dip before each failure",
             fontsize=11, color="#555555", ha="left")

    plt.tight_layout(rect=[0, 0, 1, 0.94])

    png_path = OUTPUT_DIR / "langtang_polsar_small_multiples.png"
    pdf_path = OUTPUT_DIR / "langtang_polsar_small_multiples.pdf"
    plt.savefig(png_path, dpi=300, facecolor="white")
    plt.savefig(pdf_path, facecolor="white")
    plt.close(fig)
    print(f"Saved {png_path}")
    print(f"Saved {pdf_path}")


# -----------------------------------------------------------------------
# 3. Year-over-year overlay
# -----------------------------------------------------------------------

def to_common_year_axis(date, common_year=2024):
    """Map any date onto a common leap year (2024, so Feb 29 is valid)
    for overlay plotting, keeping month/day but discarding the actual
    year."""
    return datetime(common_year, date.month, date.day)


def build_yoy_overlay(df: pd.DataFrame):
    g = df[df["zone"] == "detachment"].sort_values("date").copy()
    g["year"] = g["date"].dt.year
    g["common_date"] = g["date"].apply(lambda d: to_common_year_axis(d))

    yoy_events = [
        (2025, "2025-07-08", "Jul 8: lake outburst\n(+59 days from dip)", COLOR_2025),
        (2026, "2026-08-26", "Aug 26: glacier collapse\n(+101 days from dip)", COLOR_2026),
    ]
    yoy_minima = [
        (2025, "2025-05-10", -13.95, COLOR_2025),
        (2026, "2026-05-17", -15.83, COLOR_2026),
    ]

    fig, ax = plt.subplots(figsize=(14, 7.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbfb")

    for year, color, label in [(2025, COLOR_2025, "2025 cycle"), (2026, COLOR_2026, "2026 cycle")]:
        yearly = g[g["year"] == year].sort_values("common_date")
        ax.plot(yearly["common_date"], yearly["cross_pol_ratio_db"], color=color,
                 linewidth=2.4, marker="o", markersize=4.5, label=label, zorder=5)

    for year, date_str, value, color in yoy_minima:
        common_date = to_common_year_axis(pd.Timestamp(date_str))
        ax.scatter([common_date], [value], s=190, facecolors="none", edgecolors=color,
                   linewidths=2.3, zorder=6)

    for year, date_str, label, color in yoy_events:
        common_date = to_common_year_axis(pd.Timestamp(date_str))
        ax.axvline(common_date, color=color, linestyle="--", linewidth=1.4, alpha=0.85, zorder=3)
        y_pos = 1.0 if year == 2026 else 0.90
        ax.annotate(label, xy=(common_date, y_pos), xycoords=("data", "axes fraction"),
                    xytext=(0, 6), textcoords="offset points", fontsize=9.5,
                    fontweight="bold", color=color, ha="center", va="bottom")

    ax.set_ylabel("Cross-pol ratio, VH \u2212 VV (dB)", fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.get_xticklabels(), fontsize=10)
    ax.tick_params(axis="y", labelsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)

    ax.set_title("Same site, same calendar timing, two different years",
                 fontsize=17, fontweight="bold", pad=52, loc="left")
    ax.text(0, 1.12,
            "Detachment zone's cross-pol ratio, 2025 vs. 2026 on a shared calendar axis \u2014 "
            "both dip in mid-May, both precede failure by 2\u20133.5 months",
            transform=ax.transAxes, fontsize=11.5, color="#555555", ha="left")

    ax.legend(loc="lower right", fontsize=10.5, framealpha=0.95, edgecolor="#cccccc")
    plt.tight_layout(rect=[0, 0, 1, 0.88])

    png_path = OUTPUT_DIR / "langtang_polsar_yoy_overlay.png"
    pdf_path = OUTPUT_DIR / "langtang_polsar_yoy_overlay.pdf"
    plt.savefig(png_path, dpi=300, facecolor="white")
    plt.savefig(pdf_path, facecolor="white")
    plt.close(fig)
    print(f"Saved {png_path}")
    print(f"Saved {pdf_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    print("Building hero chart...")
    build_hero_chart(df)

    print("\nBuilding small multiples...")
    build_small_multiples(df)

    print("\nBuilding year-over-year overlay...")
    build_yoy_overlay(df)

    print("\nAll three figures saved.")


if __name__ == "__main__":
    main()
