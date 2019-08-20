#!/usr/bin/env python3

# Fix to find catchment information for applicants identified as "No catchment"
# 10 Jan 2018
# By Jack Phillips

# First run sh bin/download_data.sh

# Imports
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker
from database.address_db_declaration import Address, Applicant, Base 
import pandas as pd
from geopy.geocoders import GoogleV3 
import requests
import time
from bs4 import BeautifulSoup 

# Set up database
engine = create_engine('sqlite:///database/app_addresses.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Helper Functions
def search_lat_lon(session, lat, lon, epsilon=0.00001):
    return session.query(Address). \
        filter(Address.lat >= lat - epsilon). \
        filter(Address.lat <= lat + epsilon). \
        filter(Address.lon >= lon - epsilon). \
        filter(Address.lon <= lon + epsilon).first()
        

def search_address(session, street, zip_code):
    return session.query(Address). \
        filter(Address.street == street). \
        filter(Address.zip_code == zip_code).first()

def geocode(geo_coder, address):
    location = geo_coder.geocode(address, exactly_one=True)
    if location:
        return location.latitude, location.longitude
    else: 
        return None

# Load Data
applicants = pd.read_csv('data/no-catchment-applicants-2019-01-11.csv', parse_dates=['CreatedDate'])
# subset_columns = ['APPLICATION_ID_REF','APPLICATION_OLD_ID','STUDENT_ADDRESS_STREET1','STUDENT_ADDRESS_CITY_NAME','STUDENT_ADDRESS_ZIPCODE','CATCHMENT_NAME','STATUS','APPLICATION_SUBMISSION_DATE']
# apps = apps[subset_columns]

# applicants = apps.groupby('APPLICATION_OLD_ID').first()
# applicants = applicants[applicants['CATCHMENT_NAME'] == 'No catchment']


# For Testing
# test_address = "2936 W WISHART ST"
# test_zip = "19132"
# test_catchment = "Rhodes, EW Catchment Area"

# test_row = applicants.sample(1)
# test_row_street = test_row['STUDENT_ADDRESS_STREET1'][0]
# test_row_zip = test_row['STUDENT_ADDRESS_ZIPCODE'][0]

matched_records = 0
total_records = 0
# applicants = applicants.head()

print(f"Processing {len(applicants)} records.")
# Look up addresses in database to get lat/lon
for idx, row in applicants.iterrows():
    street = row['Street_Street_Name__c']
    zip = row['Zip_Code__c']
    total_records = total_records + 1
    result = search_address(session, street, zip)
    
    if result:
        coords = (result.lat, result.lon)
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
                applicants.loc[idx,'Catchment_Name__c'] = catchment
                matched_records = matched_records + 1
                print(f"Matched {matched_records} of {total_records}")
    else:
        print(f"Couldn't find address: {street} {zip}")

# Save application/catchment data
applicants.to_csv("applicants_with_catchments.csv", index=False)
    
# Format data for upload via Salesforce Importer
applicants = applicants.reset_index()
upload = applicants[['Id', 'Name', 'Catchment_Name__c']]
# applicants.columns = column_names = ['Name',  'Catchment_Name__c']
upload.to_csv("applicant_ids_with_catchments.csv", index=False)

