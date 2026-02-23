###################################
## 1. Import libraries
###################################

import requests
import json
import os
import time
import pandas as pd
from sqlalchemy import create_engine


###################################
## 2. Set initial vars
###################################

years_db_id = os.getenv('NOTION_DB_ID_YEARS')
api_key = os.getenv('NOTION_API_KEY')
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

headers = {
    'Authorization' : 'Bearer ' + api_key,
    'Content-type' : 'application/json',
    'Notion-Version' : '2022-06-28'
}


###################################
## 3. Create extract function
###################################

def get_years():
    """
    Extract data from the "Years" database in Notion.

    Since Notion API has request size limit of 100 rows,
    the function uses pagination variables to make multiple
    API calls untill all the data is extracted.

    Returns:
        list[dict]: A list with all rows in dictionary form.
    """
    
    url = f'https://api.notion.com/v1/databases/{years_db_id}/query'
    
    # Pagination variables to extract all rows 
    all_data = []
    has_more = True
    next_cursor = None

    # Loop through all pages
    while has_more == True:

        payload = {'page_size' : 100}                                                     # Notion API request size limit = 100

        # payload['filter'] = {'timestamp': 'last_edited_time',                           # Comment for initial load; Uncomment for incremental load
        #                     'last_edited_time': {'after': '2026-01-01T00:00:00.000Z'}       
        #                     }

        payload['sorts'] = [{'timestamp': 'created_time',
                            'direction': 'ascending'
                            }]      
        
        if next_cursor:
            payload['start_cursor'] = next_cursor

        response = requests.post(url, json=payload, headers=headers)

        data = response.json()

        all_data.extend(data['results'])
        
        # Update pagination variables
        has_more = data['has_more']
        next_cursor = data['next_cursor']
        
        # Pause to not overload the API
        time.sleep(0.4)       

    # Write the result as file
    # with open('./data/notion_years_extract.json', 'w', encoding='utf-8') as file:
    #     json.dump(all_data, file, ensure_ascii=False, indent=4)

    return all_data


###################################
## 4. Call function and load to db
###################################

# Call extract function
years = get_years()

print(f'Retrieved {len(years)} rows.') 

# Set up connection to the database
engine = create_engine(f'postgresql://{db_user}:{db_pass}@database:5432/{postgres_db}')

# Extract and name only the needed columns
db_years_data = []

for i, item in enumerate(years):
    db_years_data.append(
         {'id': item['id'],
          'title': item['properties']['Име']['title'][0]['plain_text'],
          'created_time': item['created_time'],
          'last_edited_time': item['last_edited_time']}
        )

# Create pandas dataframe
df = pd.DataFrame(db_years_data)

# Load extracted data to the postgres database
df.to_sql(name='years_src', schema='01_src', con=engine, if_exists='delete_rows', index=False)

print(df)

print("Data loaded successfully!")