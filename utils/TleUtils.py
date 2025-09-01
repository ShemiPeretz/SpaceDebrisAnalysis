import re
from typing import Optional, Tuple
import math

# Earth gravitational parameter (km^3/s^2) and mean radius (km)
MU_EARTH_KM3_S2 = 398600.4418
R_EARTH_KM = 6378.137


def parse_norad_from_tle1(line1: str) -> Optional[int]:
    """
    Extract NORAD catalog ID from TLE line 1.
    TLE line 1 pattern begins with: "1 AAAAAU ..." where AAAAA are the 5-digit sat number.
    Returns int NORAD ID or None if not found.
    """
    if not line1:
        return None
    m = re.match(r"^1\s*(\d{5})", line1.strip())
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def parse_line2_params(line2: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse inclination (deg) and mean motion (rev/day) from TLE line 2 using fixed columns.
    Line 2 columns (1-based):
      9-16: Inclination (degrees)
      53-63: Mean Motion (revs per day)
    Returns (inclination_deg, mean_motion_rev_per_day)
    """
    if not line2 or len(line2) < 63:
        return None, None
    try:
        inc_str = line2[8:16].strip()
        mm_str = line2[52:63].strip()
        inc = float(inc_str) if inc_str else None
        mm = float(mm_str) if mm_str else None
        return inc, mm
    except Exception:
        return None, None


def altitude_from_mean_motion_km(mean_motion_rev_per_day: float) -> Optional[float]:
    """
    Estimate circular-orbit altitude from mean motion (rev/day).
    a = (mu / n^2)^(1/3), where n [rad/s] = mean_motion_rev_per_day * 2pi / 86400
    altitude = a - R_earth.
    Returns altitude in km or None if input invalid.
    """
    try:
        if mean_motion_rev_per_day is None or mean_motion_rev_per_day <= 0:
            return None
        n = mean_motion_rev_per_day * 2.0 * math.pi / 86400.0
        a = (MU_EARTH_KM3_S2 / (n * n)) ** (1.0 / 3.0)
        return a - R_EARTH_KM
    except Exception:
        return None


def classify_regime(alt_km: Optional[float]) -> Optional[str]:
    """
    Classify orbital regime by altitude (simple heuristic):
      - LEO: < 2000 km
      - MEO: 2000–35786 km
      - GEO: ~35786 ± 1500 km window
      - HEO: > GEO + 1500 km
    Returns string label or None if altitude missing.
    """
    if alt_km is None:
        return None
    if alt_km < 2000:
        return "LEO"
    if abs(alt_km - 35786) <= 1500:
        return "GEO"
    if alt_km <= 35786:
        return "MEO"
    return "HEO"
