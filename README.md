# Langtang Lirung PolSAR Precursor Analysis

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Sentinel--1](https://img.shields.io/badge/data-Sentinel--1-informational)
![Google Earth Engine](https://img.shields.io/badge/platform-Google%20Earth%20Engine-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)

Dual-polarization Sentinel-1 analysis testing for a repeatable radar precursor
signal ahead of slope failures at Langtang Lirung, Nepal.

## Background

On 26 August 2026, an ice-rock avalanche detached from Langtang Lirung and
triggered a glacial lake outburst flood (GLOF) down the Lhende Khola,
striking communities in Rasuwa district. The same general area had already
been struck by a separate supraglacial lake outburst flood on 8 July 2025.

This project asks a narrow, testable question: **does the radar backscatter
signature at the detachment zone show a repeatable structural/wetness signal
in the weeks-to-months before a failure, and is that signal localized to the
failure zone rather than reflecting general regional conditions?**

## Method

- **Data**: Sentinel-1 GRD, dual-pol (VV + VH), January 2025 - August 2026,
  restricted to a single consistent orbit pass (mixing ascending/descending
  geometries produces spurious differences unrelated to real change).
- **Metric**: cross-polarization ratio (VH - VV, dB), averaged over a 500m
  buffer at each site. A more negative (lower) value indicates a smoother,
  more specular-reflecting surface (e.g. increased surface wetness); a less
  negative value indicates more structurally complex scattering (e.g.
  roughness, fracturing).
- **Sites**: one detachment zone (the reported 2026 failure point) plus two
  independent control zones at different distances (Ghenge Liru, ~3km away
  on the same massif; Gangchempo, ~15km away, a separate peak) -- chosen to
  distinguish a signal specific to the failure zone from a broader
  regional/seasonal effect.

See `shared/aoi_definitions.py` for exact coordinates and analysis windows.

## Finding

The detachment zone shows a cross-pol ratio minimum in **mid-May of both
2025 and 2026**, each preceding a failure event by roughly 2-3.5 months:

| Year | Precursor minimum | Failure event | Lead time |
|---|---|---|---|
| 2025 | -13.95 dB (May 10) | 8 Jul 2025 lake outburst | ~59 days |
| 2026 | -15.83 dB (May 17) | 26 Aug 2026 glacier collapse | ~101 days |

Both control zones stay within a narrow, flat range across the same period
(roughly -4 to -10 dB, no comparable dip).

### Full annotated time series

![Precursor finding](stage0_polsar_output/langtang_polsar_precursor_finding.png)

### Same signal, same scale, three sites

Shared y-axis across all three panels makes the dip's isolation to the
detachment zone visually unmistakable.

![Small multiples](stage0_polsar_output/langtang_polsar_small_multiples.png)

### Year-over-year overlay

2025 and 2026 cycles plotted on a shared calendar axis, directly
visualizing the replication.

![Year-over-year overlay](stage0_polsar_output/langtang_polsar_yoy_overlay.png)

## Limitations

- **n = 2.** This is a pattern consistent across two observed events at one
  site, not a statistically validated forecasting rule.
- **Two different failure mechanisms** (a hydrological lake outburst vs. a
  mechanical ice-rock avalanche) share this precursor signature, which is
  suggestive of a common root cause (spring meltwater loading) but not
  proven by this analysis alone.
- **Wet snow ambiguity**: a falling cross-pol ratio is also consistent with
  general snow wetness, not exclusively a site-specific destabilization
  signal. A supplementary Landsat-9 optical/thermal check (not included in
  this trimmed repo) found a real, physically consistent supraglacial lake
  at this site in 2025, but did not find a sustained surface lake during the
  2026 precursor window -- meaning the 2026 mechanism may involve
  subsurface/englacial water rather than a visible pooled lake.
- Cross-pol ratio is sensitive to incidence angle and orbit geometry, which
  is why the analysis is restricted to a single consistent orbit pass
  throughout.

## Repository structure

```
.
├── shared/
│   ├── aoi_definitions.py   # site coordinates, analysis windows, event dates
│   └── s1_utils.py          # Sentinel-1 orbit selection / mosaic helpers
├── stage0_polsar.py         # main analysis: pulls Sentinel-1, computes cross-pol ratio
├── stage0_polsar_visualize_all.py  # generates all three figures from the output CSV
└── stage0_polsar_output/    # CSV + PNG/PDF outputs
```
## Data Source

- European Space Agency. Copernicus Sentinel-1 (2025–2026) SAR GRD data [Data set]. Retrieved via Google Earth Engine.

## Running it

Requires a Google Earth Engine account with API access enabled.

```bash
pip install -r requirements.txt
python3 stage0_polsar.py                    # pulls data, computes cross-pol ratio, saves CSV
python3 stage0_polsar_visualize_all.py      # generates the three figures from that CSV
```

First run will prompt an Earth Engine authentication flow in your browser.

## License

MIT -- see `LICENSE`.
