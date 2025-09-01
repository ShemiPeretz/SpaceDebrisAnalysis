import os
import requests
import pandas as pd
from typing import Optional, Dict, Any, List

"""
Reusable Space-Track API client.
- Reads SPACE_TRACK_USER and SPACE_TRACK_PASS from environment variables.
- Provides functions to fetch SATCAT, latest TLEs, decay/reentry data, and public CDMs.
- Returns pandas DataFrames. No side effects on import.
"""

BASE_URL = 'https://www.space-track.org'
LOGIN_URL = f'{BASE_URL}/ajaxauth/login'
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}

class SpaceTrackAuthError(Exception):
    pass

class SpaceTrackClient:
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or os.getenv('SPACE_TRACK_USER')
        self.password = password or os.getenv('SPACE_TRACK_PASS')
        if not self.username or not self.password:
            raise SpaceTrackAuthError('Missing Space-Track credentials. Set SPACE_TRACK_USER and SPACE_TRACK_PASS.')
        self.session = requests.Session()
        self._login()

    def _login(self) -> None:
        resp = self.session.post(LOGIN_URL, headers=HEADERS, data={'identity': self.username, 'password': self.password})
        if resp.status_code != 200 or 'You must be logged in' in resp.text:
            raise SpaceTrackAuthError('Login failed. Check SPACE_TRACK_USER/SPACE_TRACK_PASS.')

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:
            pass

    def _query(self, path: str) -> requests.Response:
        url = f"{BASE_URL}{path}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp

    # Public methods
    def fetch_satcat(self, where: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        parts = ["/basicspacedata/query/class/satcat"]
        if where:
            parts.append(f"{where}")
        if limit is not None:
            parts.append(f"limit/{int(limit)}")
        parts.append("format/json")
        path = "/".join(parts)
        data = self._query(path).json()
        return pd.DataFrame(data)

    def fetch_tle_latest(self, ordinal: int = 1, norad_filter: str = ">0", where: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        parts = [
            "/basicspacedata/query/class/tle_latest",
            f"ORDINAL/{int(ordinal)}",
            f"NORAD_CAT_ID/{norad_filter}",
        ]
        if where:
            parts.append(where)
        if limit is not None:
            parts.append(f"limit/{int(limit)}")
        parts.append("format/json")
        path = "/".join(parts)
        data = self._query(path).json()
        return pd.DataFrame(data)

    def fetch_decay(self, epoch_since: str = "now-5 years", where: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        # epoch_since uses Space-Track time math format, e.g., now-5%20years
        epoch_since_enc = epoch_since.replace(' ', '%20')
        parts = [
            "/basicspacedata/query/class/decay",
            # Use DECAY predicate (not EPOCH). Encode '>' as %3E
            f"DECAY/%3E" + epoch_since_enc,
        ]
        if where:
            parts.append(where)
        if limit is not None:
            parts.append(f"limit/{int(limit)}")
        parts.append("format/json")
        path = "/".join(parts)
        data = self._query(path).json()
        return pd.DataFrame(data)

    def fetch_cdm_public(self, created_since: str = "now-30 days", where: Optional[str] = None, limit: Optional[int] = None) -> pd.DataFrame:
        created_since_enc = created_since.replace(' days', '')
        parts = [
            "/basicspacedata/query/class/cdm_public",
            f"CREATED/>" + created_since_enc,
        ]
        if where:
            parts.append(where)
        if limit is not None:
            parts.append(f"limit/{int(limit)}")
        parts.append("format/json")
        path = "/".join(parts)
        data = self._query(path).json()
        return pd.DataFrame(data)

    def fetch_tle_by_id(self, norad_cat_id: int, orderby: str = "EPOCH desc", limit: Optional[int] = None) -> pd.DataFrame:
        orderby_enc = orderby.replace(' ', '%20')
        parts = [
            "/basicspacedata/query/class/tle",
            f"NORAD_CAT_ID/{int(norad_cat_id)}",
            f"orderby/{orderby_enc}",
        ]
        if limit is not None:
            parts.append(f"limit/{int(limit)}")
        parts.append("format/json")
        path = "/".join(parts)
        data = self._query(path).json()
        df = pd.DataFrame(data)
        df.to_csv(f"..\\DATA\\tles_{norad_cat_id}.csv", index=False)
        return df

    def fetch_tle_by_id_and_epoch(self, norad_cat_id: int, epoch_start: Optional[str] = None, epoch_end: Optional[str] = None, orderby: str = "EPOCH desc", limit: Optional[int] = None) -> pd.DataFrame:
        """
        Fetches historical TLEs for a specific NORAD_CAT_ID, with optional epoch filtering.

        Args:
            norad_cat_id: The NORAD Catalog ID of the satellite.
            epoch_start: Optional start date for epoch filter (e.g., "2025-08-01").
            epoch_end: Optional end date for epoch filter (e.g., "2025-08-31").
            orderby: The field to sort by (e.g., "EPOCH desc").
            limit: The maximum number of records to return.

        Returns:
            A pandas DataFrame containing the TLE data.
        """
        orderby_enc = orderby.replace(' ', '%20')
        parts = [
            "/basicspacedata/query/class/tle",
            f"NORAD_CAT_ID/{int(norad_cat_id)}",
        ]

        # Add epoch filter if provided, using Space-Track's range format.
        if epoch_start and epoch_end:
            parts.append(f"EPOCH/{epoch_start}--{epoch_end}")
        elif epoch_start:
            parts.append(f"EPOCH/>{epoch_start}")
        elif epoch_end:
            parts.append(f"EPOCH/<{epoch_end}")

        parts.append(f"orderby/{orderby_enc}")

        if limit is not None:
            parts.append(f"limit/{int(limit)}")

        parts.append("format/json")
        path = "/".join(parts)
        data = self._query(path).json()
        df = pd.DataFrame(data)
        df.to_csv(f"tles_{norad_cat_id}_epoch_{epoch_start}.csv", index=False)
        return df

# Convenience function for context manager usage
class space_track_client:
    def __enter__(self) -> "SpaceTrackClient":
        self.client = SpaceTrackClient()
        return self.client
    def __exit__(self, exc_type, exc, tb):
        self.client.close()
        return False

if __name__ == "__main__":
    # Minimal demo: try to fetch a few rows from SATCAT if credentials are set.
    try:
        with space_track_client() as st:
            df = st.fetch_tle_by_id_and_epoch(58074, "2025-08-16", "2025-08-18")
            print("tle sample:")
            print(df.head())
    except SpaceTrackAuthError as e:
        print("Space-Track credentials not set or login failed:", e)
