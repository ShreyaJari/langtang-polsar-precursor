"""
shared/aoi_definitions.py

Single source of truth for all AOI coordinates used across Stage 0
strands (PolSAR, Landsat, InSAR stack, synthesis). Defining these once
here -- rather than duplicating coordinates in each strand script --
means updating the detachment point or control zones updates every
strand automatically instead of risking silent drift between scripts.
"""

# Reported detachment point (26 Aug 2026 collapse), per NYT reporting
# referenced in the Spatial Sense LinkedIn analysis.
DETACHMENT_POINT = {
    "name": "detachment",
    "lon": 85.525,
    "lat": 28.285,
}

# Control zones, chosen at two different scales to separate
# "was it specific to this one face" from "was it broader regional
# melt":
#
#   ghenge_liru: Langtang Lirung's own subsidiary peak, only ~3 km
#   away, same immediate massif. If this shows the same acceleration
#   as the detachment point, the signal (whatever it is) isn't
#   specific to the failed face -- it's massif-wide.
#
#   gangchempo: a separate peak/glacier system ~15 km east, across the
#   valley (also visible as a labeled landmark in the Spatial Sense
#   slide itself). If THIS also shows the same trend, the signal is
#   regional (e.g. a hot melt season across Langtang Himal generally),
#   not localized to Langtang Lirung at all.
CONTROL_ZONES = [
    {"name": "ghenge_liru", "lon": 85.470848, "lat": 28.247802},
    {"name": "gangchempo", "lon": 85.681110, "lat": 28.168890},
]

# Buffer radius (meters) around each point above, defining the small
# AOI polygon used for pixel-level extraction in the PolSAR strand
# (stage0_polsar.py).
POINT_BUFFER_M = 500

# Larger buffer for the Landsat lake-detection strand (stage0_landsat.py).
# A supraglacial lake may form near, not exactly at, the detachment
# point, and Landsat's coarser 30m pixels need more area to give a
# meaningful pixel count for a water-fraction estimate.
LAKE_BUFFER_M = 1000

# Source glacier corridor AOI, for wider-area context maps.
# TODO: confirm against LiCSAR frame 085A_06253_131313 footprint.
GLACIER_AOI_BOUNDS = {
    "west": 85.45,
    "east": 85.58,
    "south": 28.24,
    "north": 28.32,
}

# Shared analysis window, matching the Spatial Sense comparison.
ANALYSIS_START = "2025-01-01"
ANALYSIS_END = "2026-08-31"

# Melt-season windows for year-over-year comparison.
MELT_SEASON_2025 = ("2025-04-01", "2025-08-31")
MELT_SEASON_2026 = ("2026-04-01", "2026-08-31")

EVENT_DATE = "2026-08-26"

# Specific window flagged by the PolSAR strand's cross-pol ratio minimum
# (detachment zone, 2026) -- the window Strand 3 should scrutinize most
# closely for a supraglacial lake signal.
POLSAR_FLAGGED_WINDOW = ("2026-04-15", "2026-06-15")