#!/usr/bin/env python3

# Run in the acadonda3 cd .\Anaconda3\
# comand in terminal is ./python "Path.py"


# Imports
import pandas as pd 
import requests
import time
from bs4 import BeautifulSoup 



# Load Data
applicants = pd.read_csv('Z:/Data and Analytics/APC/Kipp Address Match/KIPP Addresses with LAt Long.csv')


matched_records = 0
total_records = len(applicants)

print(f"Processing {len(applicants)} records.")
# Look up addresses in database to get lat/lon
for idx, row in applicants.iterrows():
    if True:
        coords = (row['latitude'], row['longitude'])
        timestamp = int(time.time())
        url = f"https://webapps1.philasd.org/school_finder/ajax/pip/{coords[0]}/{coords[1]}/{timestamp}"
        print(f"Found address. Pinging {url}")
    
        # Call school finder to pull catchment name
        response = requests.get(url)
        if response.ok:
            soup = BeautifulSoup(response.content, 'html.parser')
            if soup.h3:
                catchment = soup.h3.contents[0]
                print(f"Found catchment: {catchment}")
                # Add catchment name to applicant data
                applicants.loc[idx,'Catchment_Name'] = catchment
                matched_records = matched_records + 1
                print(f"Matched {matched_records} of {total_records}")

# Save application/catchment data
applicants.to_csv("applicants_with_catchments.csv", index=False)
    
