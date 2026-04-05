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

budgets_db_id = os.getenv('NOTION_DB_ID_BUDGETS')
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

###################################
## 4. Call function and load to db
###################################

# Call extract function
budgets = get_data(budgets_db_id)

# For testing purposes during development
# with open('./data/notion_budgets_extract.json', 'r', encoding='utf-8') as file:
#   budgets = json.load(file)

print(f'Retrieved {len(budgets)} rows.') 

# Set up connection to the budget-db
engine = create_engine(f'postgresql://{db_user}:{db_pass}@budget-db:5432/{postgres_db}')

# Extract and name only the needed columns
db_budgets_data = []

for i, item in enumerate(budgets):
    db_budgets_data.append(
         {
          'id':                item['id']                                                                                                                                   ,
          'title':             item['properties']['Name']['title'][0]['plain_text']                        if item['properties']['Name']['title']                 else None ,
          'budget_amnt':       item['properties']['Бюджет']['number']                                                                                                       ,
          'year_id':           item['properties']['Година']['relation'][0]['id']                           if item['properties']['Година']['relation']            else None ,
          'month_id':          item['properties']['Месец']['relation'][0]['id']                            if item['properties']['Месец']['relation']             else None ,
          'category_id':       item['properties']['Категория']['rollup']['array'][0]['relation'][0]['id']  if item['properties']['Категория']['rollup']['array']  else None ,
          'subcategory_id':    item['properties']['Подкатегория']['relation'][0]['id']                     if item['properties']['Подкатегория']['relation']      else None ,
          'is_archived':       item['properties']['Скрита']['checkbox']                                                                                                     ,
          'created_time':      item['created_time']                                                                                                                         ,
          'last_edited_time':  item['last_edited_time']                                                                                                                     
          }
        )

# Create pandas dataframe
df = pd.DataFrame(db_budgets_data)

# During development, because Airflow comes with pandas v2.3, which doesn't support to_sql(if_exists='delete_rows')
with engine.begin() as conn: 
  conn.execute(text('DELETE FROM "raw"."budget"'))

# Load extracted data to the postgres budget-db
df.to_sql(name='budget', schema='raw', con=engine, if_exists='append', index=False)

print(f"Loaded {len(budgets)} rows successfully!")