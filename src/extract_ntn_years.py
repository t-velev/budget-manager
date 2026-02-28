###########################################
## 1. Import libraries
###########################################

import os
import pandas as pd
from ntn_utils import get_data
from sqlalchemy import create_engine

###########################################
## 2. Set initial vars
###########################################

years_db_id = os.getenv('NOTION_DB_ID_YEARS')
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

###########################################
## 3. Call extract function and load to db
###########################################

# Call extract function
years = get_data(years_db_id)

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