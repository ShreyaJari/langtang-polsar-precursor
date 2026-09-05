#!/usr/bin/env python3
"""
stage0_polsar.py

Strand 2 of the Stage 0 precursor investigation: dual-pol Sentinel-1
cross-pol ratio (VH - VV, in dB) as a structural/roughness change
indicator, compared between the detachment zone and two control zones
at different spatial scales (see shared/aoi_definitions.py for the
reasoning behind ghenge_liru vs gangchempo).

Method
------
Cross-pol ratio rises when a surface shifts toward more volume
scattering relative to smooth surface scattering -- i.e. when it gets
rougher, more fractured, or more structurally complex. A glacier
surface progressively crevassing or destabilizing in the lead-up to
failure would plausibly show a RISING cross-pol ratio trend, distinct
from a stable or seasonally-flat trend at unaffected control areas.

Because Sentinel-1 GRD bands from COPERNICUS/S1_GRD are already in dB,
VH - VV directly gives the ratio in dB (10*log10(VH/VV) =
VH_dB - VV_dB) -- no natural-unit conversion needed here, unlike the
Refined Lee filtering in Stage 3.

Each point AOI is a small buffered polygon (POINT_BUFFER_M), and each
per-scene value is a spatial MEAN over that polygon via reduceRegions
-- this already pools many pixels per date, which suppresses speckle
without needing the heavier Refined Lee filter (see shared/s1_utils.py
docstring note).

LIMITATIONS -- state these explicitly in any writeup:
- Wet snow also raises cross-pol ratio, independent of any fracturing
  or crevassing. A rise during the melt season is ambiguous between
  "more melt saturation" and "more structural disturbance" on its own
  -- this is why the synthesis step (stage0_synthesis.py) matters:
  agreement with the InSAR/Landsat strands is what disambiguates it,
  not this strand alone.
- Cross-pol ratio is sensitive to incidence angle and orbit geometry,
  same as backscatter was for the Stage 3 flood mask -- restricted to
  a single consistent orbit pass throughout for this reason.
- A rising ratio at the detachment point that ALSO rises equally at
  both control zones indicates a general phenomenon (e.g. regional hot
  melt season), not a localized precursor -- check this explicitly,
  don't just report the detachment-point trend in isolation.

Requirements
------------
    conda activate nepal-flood

Usage
-----
    python3 stage0_polsar.py
"""

import sys
from pathlib import Path

import ee
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared.aoi_definitions import (
    DETACHMENT_POINT, CONTROL_ZONES, POINT_BUFFER_M,
    ANALYSIS_START, ANALYSIS_END, MELT_SEASON_2025, MELT_SEASON_2026,
    EVENT_DATE,
)
from shared.s1_utils import get_s1_collection_info, pick_consistent_orbit

OUTPUT_DIR = Path.home() / "_GeoAI_Notebook" / "langtang-polsar-precursor" / "stage0_polsar_output"

EE_PROJECT = "carbon-verification-toolkit"  # matches Stage 3's project


def build_zones_fc():
    """Build a labeled FeatureCollection of buffered point AOIs: the
    detachment point plus every control zone from CONTROL_ZONES."""
    all_points = [DETACHMENT_POINT] + CONTROL_ZONES
    features = []
    for p in all_points:
        geom = ee.Geometry.Point([p["lon"], p["lat"]]).buffer(POINT_BUFFER_M)
        features.append(ee.Feature(geom, {"name": p["name"]}))
    return ee.FeatureCollection(features), all_points


def build_combined_aoi(all_points):
    """Union of all point buffers, for collection filterBounds -- wide
    enough to cover every zone, used only for filtering, not for any
    heavy per-pixel computation."""
    geoms = [ee.Geometry.Point([p["lon"], p["lat"]]).buffer(POINT_BUFFER_M)
             for p in all_points]
    combined = geoms[0]
    for g in geoms[1:]:
        combined = combined.union(g, maxError=1)
    return combined


def extract_time_series(collection: ee.ImageCollection, zones_fc: ee.FeatureCollection) -> pd.DataFrame:
    """
    For every image in the collection, reduce VV and VH to a spatial
    mean over each zone polygon, tagging each result with the image's
    acquisition date. Returns a long-format DataFrame: one row per
    (date, zone).
    """
    def per_image(image):
        date_str = image.date().format("YYYY-MM-dd")
        stats = image.reduceRegions(
            collection=zones_fc,
            reducer=ee.Reducer.mean(),
            scale=10,
        )
        return stats.map(lambda f: f.set("date", date_str))

    results_fc = collection.map(per_image).flatten()

    print("  Pulling per-scene zone statistics from Earth Engine (this can take a minute)...")
    features = results_fc.getInfo()["features"]

    rows = []
    for feat in features:
        props = feat["properties"]
        rows.append({
            "date": props.get("date"),
            "zone": props.get("name"),
            "VV": props.get("VV"),
            "VH": props.get("VH"),
        })

    df = pd.DataFrame(rows)
    n_before = len(df)
    df = df.dropna(subset=["VV", "VH"])
    n_after = len(df)
    print(f"  Extracted {n_before} (zone, date) rows; {n_after} with valid VV+VH "
          f"({n_before - n_after} dropped -- likely edge-of-scene or no-data pixels).")

    df["date"] = pd.to_datetime(df["date"])
    df["cross_pol_ratio_db"] = df["VH"] - df["VV"]
    return df.sort_values(["zone", "date"]).reset_index(drop=True)


def plot_time_series(df: pd.DataFrame, out_path: Path):
    fig, ax = plt.subplots(figsize=(11, 6))

    for melt_start, melt_end in [MELT_SEASON_2025, MELT_SEASON_2026]:
        ax.axvspan(pd.Timestamp(melt_start), pd.Timestamp(melt_end),
                    color="orange", alpha=0.08, zorder=0)

    ax.axvline(pd.Timestamp(EVENT_DATE), color="red", linestyle="--",
               linewidth=1, label=f"{EVENT_DATE} collapse", zorder=1)

    colors = {"detachment": "#c0392b", "ghenge_liru": "#2980b9", "gangchempo": "#27ae60"}
    for zone, group in df.groupby("zone"):
        color = colors.get(zone, None)
        ax.plot(group["date"], group["cross_pol_ratio_db"], marker="o", markersize=3,
                 linewidth=1, alpha=0.7, label=zone, color=color)

    ax.set_xlabel("Date")
    ax.set_ylabel("Cross-pol ratio, VH - VV (dB)")
    ax.set_title("Dual-pol Sentinel-1 cross-pol ratio: detachment vs. control zones")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(loc="upper left")
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"  Saved plot to {out_path}")


def summarize_melt_seasons(df: pd.DataFrame):
    print("\n--- Melt-season mean cross-pol ratio by zone ---")
    for label, (start, end) in [("2025", MELT_SEASON_2025), ("2026", MELT_SEASON_2026)]:
        mask = (df["date"] >= start) & (df["date"] <= end)
        season_df = df[mask]
        print(f"\n  {label} melt season ({start} to {end}):")
        for zone, group in season_df.groupby("zone"):
            print(f"    {zone}: mean={group['cross_pol_ratio_db'].mean():.2f} dB, "
                  f"n={len(group)}")


def main():
    print("Initializing Earth Engine...")
    ee.Initialize(project=EE_PROJECT)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    zones_fc, all_points = build_zones_fc()
    combined_aoi = build_combined_aoi(all_points)

    print(f"\nZones: {[p['name'] for p in all_points]}")
    print(f"Window: {ANALYSIS_START} to {ANALYSIS_END}")

    print("\nChecking orbit pass availability...")
    raw_collection = get_s1_collection_info(combined_aoi, ANALYSIS_START, ANALYSIS_END, bands=("VV", "VH"))
    orbit_pass = pick_consistent_orbit(raw_collection, raw_collection)  # single collection, just inspecting

    collection = raw_collection.filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
    count = collection.size().getInfo()
    print(f"  {count} scene(s) on orbit pass {orbit_pass} over the full window.")
    if count == 0:
        raise RuntimeError("No scenes found -- check AOI/date window/orbit availability.")

    df = extract_time_series(collection, zones_fc)

    csv_path = OUTPUT_DIR / "stage0_polsar_timeseries.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nSaved time series CSV to {csv_path}")

    plot_path = OUTPUT_DIR / "stage0_polsar_timeseries.png"
    plot_time_series(df, plot_path)

    summarize_melt_seasons(df)


if __name__ == "__main__":
    main()