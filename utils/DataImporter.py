import pandas as pd
from pathlib import Path

from APIs.CelesTrakAPI import fetch_debris_groups as ct_fetch, save_tles as ct_save
from APIs.SpaceTrackAPI import SpaceTrackClient, SpaceTrackAuthError

DATA_DIR = Path("../DATA")
DATA_DIR.mkdir(exist_ok=True)


def save_df(df: pd.DataFrame, name: str) -> None:
    out_path = DATA_DIR / name
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")


def fetch_celestrak_debris():
    print("Fetching CelesTrak debris group TLEs...")
    df = ct_fetch()
    # Save TLEs also to extracted_tles for convenience
    ct_save(df)
    save_df(df, "celestrak_debris_tles.csv")


def fetch_spacetrack_sets():
    print("Fetching Space-Track datasets...")
    try:
        st = SpaceTrackClient()
    except SpaceTrackAuthError as e:
        print("Skipping Space-Track fetch:", e)
        return

    try:
        cdm = st.fetch_cdm_public(created_since="now-100 days")
        save_df(cdm, "spacetrack_cdm_public_100d.csv")
    finally:
        try:
            st.close()
        except Exception:
            pass