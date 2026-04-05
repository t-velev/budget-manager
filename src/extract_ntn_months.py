###################################
## 1. Import libraries
###################################

import os
import pandas as pd
from ntn_utils import get_data
from sqlalchemy import create_engine, text

###################################
## 2. Set initial vars
###################################

months_db_id = os.getenv('NOTION_DB_ID_MONTHS')
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

###################################
## 4. Call function and load to db
###################################

# Call extract function
months = get_data(months_db_id)

# For testing purposes during development
# with open('./data/notion_months_extract.json', 'r', encoding='utf-8') as file:
#   months = json.load(file)

print(f'Retrieved {len(months)} rows.') 

# Set up connection to the budget-db
engine = create_engine(f'postgresql://{db_user}:{db_pass}@budget-db:5432/{postgres_db}')

# Extract and name only the needed columns
db_months_data = []

for i, item in enumerate(months):
    db_months_data.append(
         {
          'id':                item['id']                                                                                            ,
          'title':             item['properties']['Name']['title'][0]['plain_text'] if item['properties']['Name']['title'] else None ,
          'created_time':      item['created_time']                                                                                  ,
          'last_edited_time':  item['last_edited_time']                                                                                                                     
          }
        )

# Create pandas dataframe
df = pd.DataFrame(db_months_data)

# During development, because Airflow comes with pandas v2.3, which doesn't support to_sql(if_exists='delete_rows')
with engine.begin() as conn: 
  conn.execute(text('DELETE FROM "raw"."month"'))

# Load extracted data to the postgres budget-db
df.to_sql(name='month', schema='raw', con=engine, if_exists='append', index=False)

print(f"Loaded {len(months)} rows successfully!")