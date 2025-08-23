import os
import pandas as pd
import requests

# Directory containing the TLE files
TLE_DIR = 'SpaceX_Ephemeris_552_SpaceX_2025-07-11UTC05_21_04_01'
OUTPUT_DIR = 'extracted_tles'
CSV_OUTPUT = 'all_tles.csv'

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Replace with your Space-Track.org credentials
USERNAME = 'your_username'
PASSWORD = 'your_password'

# Example: Fetch latest TLEs for all active satellites
LOGIN_URL = 'https://www.space-track.org/ajaxauth/login'
TLE_URL = (
    'https://www.space-track.org/basicspacedata/query/class/tle_latest/'
    'ORDINAL/1/NORAD_CAT_ID/>0/format/tle'
)

def is_tle_line(line):
    # TLE lines typically start with 1 or 2 and are 69-70 chars long
    return (line.startswith('1 ') or line.startswith('2 ')) and len(line.strip()) >= 68

def extract_tle_sets(file_path):
    tle_sets = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines) - 2:
        # Look for a TLE set: name, line1, line2
        if is_tle_line(lines[i+1]) and is_tle_line(lines[i+2]):
            tle_sets.append((lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()))
            i += 3
        else:
            i += 1
    return tle_sets

def fetch_tle():
    with requests.Session() as session:
        # Login
        login_data = {'identity': USERNAME, 'password': PASSWORD}
        resp = session.post(LOGIN_URL, data=login_data)
        if resp.status_code != 200 or 'You must be logged in' in resp.text:
            raise Exception('Login failed. Check your credentials.')

        # Fetch TLE data
        tle_resp = session.get(TLE_URL)
        if tle_resp.status_code == 200:
            print("TLE data fetched successfully.")
            print(tle_resp.text[:1000])  # Print first 1000 chars as a sample
            # You can save or process tle_resp.text as needed
        else:
            print(f"Failed to fetch TLEs: {tle_resp.status_code}")

def main():
    all_tles = []
    for filename in os.listdir(TLE_DIR):
        if filename.endswith('.txt'):
            file_path = os.path.join(TLE_DIR, filename)
            tle_sets = extract_tle_sets(file_path)
            print(f"{filename}: {len(tle_sets)} TLE sets found.")
            # Save extracted TLEs to a new file
            output_path = os.path.join(OUTPUT_DIR, filename.replace('.txt', '_tles.txt'))
            with open(output_path, 'w') as out:
                for name, line1, line2 in tle_sets:
                    out.write(f"{name}\n{line1}\n{line2}\n\n")
                    all_tles.append({'file': filename, 'name': name, 'line1': line1, 'line2': line2})
    # Create DataFrame and save as CSV
    df = pd.DataFrame(all_tles, columns=['file', 'name', 'line1', 'line2'])
    print(df.head())
    df.to_csv(CSV_OUTPUT, index=False)
    print(f"Saved all TLEs to {CSV_OUTPUT}")

if __name__ == '__main__':
    main() 