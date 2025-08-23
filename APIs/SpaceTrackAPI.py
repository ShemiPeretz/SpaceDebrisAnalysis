import requests
import json
import pandas as pd

# Your Space-Track credentials
USERNAME = 'pershi@post.bgu.ac.il'
PASSWORD = 'asdfghjkL!1234_5678'

# Base URL and endpoints
BASE_URL = 'https://www.space-track.org'
LOGIN_URL = f'{BASE_URL}/ajaxauth/login'

# Headers
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}

# Login session
session = requests.Session()
login_data = {
    'identity': USERNAME,
    'password': PASSWORD
}
resp = session.post(LOGIN_URL, headers=HEADERS, data=login_data)

if resp.status_code != 200:
    raise Exception("Login failed. Check credentials.")

print("✅ Logged in successfully.")

test_url = "https://www.space-track.org/basicspacedata/query/class/satcat/limit/1/format/json"
resp = session.get(test_url)

if resp.status_code == 200:
    print("✅ Authenticated query worked. Sample result:")
    print(resp.json()[0])
else:
    print("❌ Query failed:", resp.status_code, resp.text)

# # --- Fetch TLEs (active objects in last 7 days) ---
# tle_url = f"{BASE_URL}/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/>0/format/json"
# tle_resp = session.get(tle_url)
#
# print(tle_resp.status_code)
# print(tle_resp.text)  # See what's coming back
#
# tle_data = tle_resp.json()
# # Example for TLEs
# if tle_data:
#     pd.DataFrame(tle_data).to_csv("tle_latest.csv", index=False)
#     print(f"📦 TLE data saved. {len(tle_data)} records.")
# else:
#     print("⚠️ No TLE data returned.")
#
# # --- Fetch SATCAT metadata ---
# satcat_url = f"{BASE_URL}/basicspacedata/query/class/satcat/format/json"
# satcat_resp = session.get(satcat_url)
# satcat_data = satcat_resp.json()
# pd.DataFrame(satcat_data).to_csv("satcat.csv", index=False)
# print(f"📦 SATCAT data saved. {len(satcat_data)} records.")
#
# # --- Fetch Decay/Reentry data (last 5 years) ---
# decay_url = f"{BASE_URL}/basicspacedata/query/class/decay/EPOCH/>now-5%20years/format/json"
# decay_resp = session.get(decay_url)
# decay_data = decay_resp.json()
# pd.DataFrame(decay_data).to_csv("decay_data.csv", index=False)
# print(f"📦 Decay data saved. {len(decay_data)} records.")

# Optional: close session
session.close()
