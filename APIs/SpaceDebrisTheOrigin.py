import pandas as pd
import os
from glob import glob

# Define the directory containing your .dat files
directory = '../space-debris-the-origin/deb_test/'  # Update this path if needed

# Pattern to match all relevant .dat files
pattern = os.path.join(directory, 'eledebnewfd*.dat')

# Get a sorted list of all matching .dat files
dat_files = sorted(glob(pattern))

# Read and combine all .dat files into one DataFrame
combined_df = pd.concat(
    (pd.read_fwf(f, header=None) for f in dat_files),
    ignore_index=True
)

# Assign descriptive column names
combined_df.columns = [
    'Object_ID_or_EpochOffset',
    'Julian_Date',
    'Eccentricity',
    'Inclination_deg',
    'RAAN_deg',
    'Arg_of_Perigee_deg',
    'Mean_Anomaly_deg'
]

# Optional: Save to CSV
combined_df.to_csv('../DATA/space_debris_the_origin_test.csv', index=False)

# Display the first few rows
print(combined_df.head())

