import os
import pandas as pd
from pathlib import Path

# Local imports
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
    print("Fetching Space-Track datasets (if credentials available)...")
    try:
        st = SpaceTrackClient()
    except SpaceTrackAuthError as e:
        print("Skipping Space-Track fetch:", e)
        return

    try:
        # # SATCAT metadata (limit for quick EDA start)
        # satcat = st.fetch_satcat(limit=20000)
        # save_df(satcat, "spacetrack_satcat.csv")
        #
        # # Latest TLEs snapshot (ordinal 1). Keep limit moderate to avoid huge downloads.
        # tles = st.fetch_tle_latest(ordinal=1, norad_filter=">0", limit=20000)
        # save_df(tles, "spacetrack_tle_latest.csv")
        #
        # # Decay / reentry for last 5 years
        # decay = st.fetch_decay(epoch_since="now-5 years")
        # save_df(decay, "spacetrack_decay_5y.csv")

        # Public CDMs (last 30 days). Often useful for conjunction statistics.
        cdm = st.fetch_cdm_public(created_since="now-100 days")
        save_df(cdm, "spacetrack_cdm_public_100d.csv")
    finally:
        try:
            st.close()
        except Exception:
            pass


def main():
    fetch_celestrak_debris()
    fetch_spacetrack_sets()
    print("Data fetch complete.")


if __name__ == "__main__":
    main()
