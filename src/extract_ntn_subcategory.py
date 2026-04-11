#######################################################
## 1. Import libraries
#######################################################

import os
import pandas as pd
from ntn_utils import get_data, get_last_load_date, load_new_data, del_missing_data
from sqlalchemy import create_engine

#######################################################
## 2. Set initial vars
#######################################################

subcategory_db_id = os.getenv('NOTION_DB_ID_SUBCATEGORY')
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

pg_schema = 'raw'
pg_table_name = 'subcategory'

#######################################################
## 3. Load new data
#######################################################

# Set up connection to the budget-db
engine = create_engine(f'postgresql://{db_user}:{db_pass}@budget-db:5432/{postgres_db}')

# Get the last load date from the database
last_load_date = get_last_load_date(pg_schema, pg_table_name, engine)

print('Last load date = ', last_load_date)

new_data_filter = ['Име', 'Тип', 'Сметка', 'Категория', 'Необходимост', 'Падеж', 'Архивирай']  # A list of notion db column names to be filtered. Empty list filters nothing.

# Extract ONLY NEW data, no filters
subcategory_new_data = get_data(subcategory_db_id, last_load_date, filter_cols=new_data_filter)

# For testing purposes during development
# with open('./data/notion_subcategory_extract.json', 'r', encoding='utf-8') as file:
#   subcategory_new_data = json.load(file)

print(f'Retrieved {len(subcategory_new_data)} new rows from Notion.')

# Extract and name only the needed columns
new_data = []

for i, item in enumerate(subcategory_new_data):
    new_data.append(
         {
          'id':                item['id']                                                                                                     ,
          'title':             item['properties']['Име']['title'][0]['plain_text']  if item['properties']['Име']['title']           else None ,
          'type':              item['properties']['Тип']['select']['name']          if item['properties']['Тип']['select']          else None ,
          'account_id':        item['properties']['Сметка']['relation'][0]['id']    if item['properties']['Сметка']['relation']     else None ,
          'category_id':       item['properties']['Категория']['relation'][0]['id'] if item['properties']['Категория']['relation']  else None ,
          'flex_type':         item['properties']['Необходимост']['select']['name'] if item['properties']['Необходимост']['select'] else None ,
          'due_date':          item['properties']['Падеж']['date']['start']         if item['properties']['Падеж']['date']          else None ,
          'is_archived':       item['properties']['Архивирай']['checkbox']                                                                    ,
          'created_time':      item['created_time']                                                                                           ,
          'last_edited_time':  item['last_edited_time']
          }
        )

# Create pandas dataframe
new_data_df = pd.DataFrame(new_data)

# Load the new data and capture the result
loaded_count = load_new_data(pg_schema, pg_table_name, new_data_df, engine)

print(f'Loaded {loaded_count} rows into {pg_schema}.{pg_table_name}!')

#######################################################
## 4. Extract and load ids
#######################################################

# Extracting all the records in the table, but only one column,
# so we can get the id (it's outside of the properties/columns list).
# Then we use the the audit list of ids to find and delete the missing rows
# in the raw schema's tables.

id_cols_filter = ['Име']  # A list of notion db column names to be filtered. Empty list filters nothing.

# Extract ALL data, filtered Name column
filtered_data = get_data(subcategory_db_id, last_load_date=None, filter_cols=id_cols_filter)

# For testing purposes during development
# with open('./data/notion_subcategory_extract.json', 'r', encoding='utf-8') as file:
#   subcategory_new_data = json.load(file)

print(f'Retrieved {len(filtered_data)} filtered rows from Notion.')

filtered_data_df = []

for i, item in enumerate(filtered_data):
    filtered_data_df.append(
         {
          'id':          item['id']                                                                                          ,
          'title':       item['properties']['Име']['title'][0]['plain_text'] if item['properties']['Име']['title'] else None ,
          'source_name': pg_table_name
          }
        )

#######################################################
## 5. Delete missing data in the source from the target
#######################################################

# Create pandas dataframe
filtered_df = pd.DataFrame(filtered_data_df)

# Call delete function and capture the result
deleted_count = del_missing_data(pg_schema, pg_table_name, filtered_df, engine)

print(f'Deleted {deleted_count} rows from {pg_schema}.{pg_table_name}!')