import requests
import pandas as pd
from typing import List, Tuple
import os

"""
CelesTrak client for pulling debris-group TLEs.
No authentication required.
Outputs EDA-friendly DataFrame with columns: group, name, line1, line2.
"""

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
DEFAULT_DEBRIS_GROUPS = [
    # Major debris clouds
    "iridium-33-debris",
    "cosmos-2251-debris",
    "fengyun-1c-debris",
    # Other historical breakups
    "cosmos-1408-debris",  # 2021 ASAT event
    "2012-044-debris",     # Breeze-M breakup
]


def fetch_group_tle(group: str) -> str:
    params = {"GROUP": group, "FORMAT": "tle"}
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.text


def parse_tle_text(tle_text: str, group: str) -> List[Tuple[str, str, str, str]]:
    lines = [l.rstrip("\r\n") for l in tle_text.splitlines() if l.strip()]
    records: List[Tuple[str, str, str, str]] = []
    i = 0
    while i + 2 < len(lines):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]
        if (line1.startswith("1 ") and line2.startswith("2 ")):
            records.append((group, name, line1, line2))
            i += 3
        else:
            # If misaligned, try to advance by one line
            i += 1
    return records


def fetch_debris_groups(groups: List[str] = None) -> pd.DataFrame:
    if groups is None:
        groups = DEFAULT_DEBRIS_GROUPS
    all_records: List[Tuple[str, str, str, str]] = []
    for g in groups:
        tle_text = fetch_group_tle(g)
        recs = parse_tle_text(tle_text, g)
        all_records.extend(recs)
    df = pd.DataFrame(all_records, columns=["group", "name", "line1", "line2"])
    return df


def save_tles(df: pd.DataFrame, out_dir: str = "extracted_tles", basename: str = "celestrak_debris") -> None:
    os.makedirs(out_dir, exist_ok=True)
    # Save combined CSV
    csv_path = os.path.join(out_dir, f"{basename}.csv")
    df.to_csv(csv_path, index=False)
    # Save per-group TLE text files (optional, helpful for tools expecting TLE format)
    for group, gdf in df.groupby("group"):
        txt_path = os.path.join(out_dir, f"{basename}_{group}.tle")
        with open(txt_path, "w") as f:
            for _, row in gdf.iterrows():
                f.write(f"{row['name']}\n{row['line1']}\n{row['line2']}\n")


if __name__ == "__main__":
    df = fetch_debris_groups()
    print(df.head())
    save_tles(df)
