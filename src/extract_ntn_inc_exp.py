###################################
## 1. Import libraries
###################################

import os
import pandas as pd
from ntn_utils import get_data
from sqlalchemy import create_engine

###################################
## 2. Set initial vars
###################################

inc_exp_db_id = os.getenv('NOTION_DB_ID_INC_EXP')
postgres_db = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')

###################################
## 4. Call function and load to db
###################################

# Call extract function
inc_exp = get_data(inc_exp_db_id)

# For testing purposes during development
# with open('./data/notion_inc_exp_extract.json', 'r', encoding='utf-8') as file:
#   inc_exp = json.load(file)

print(f'Retrieved {len(inc_exp)} rows.') 

# Set up connection to the database
engine = create_engine(f'postgresql://{db_user}:{db_pass}@database:5432/{postgres_db}')

# Extract and name only the needed columns
db_inc_exp_data = []

for i, item in enumerate(inc_exp):
    db_inc_exp_data.append(
         {
          'id':                item['id']                                                                                                                                   ,
          'title':             item['properties']['Name']['title'][0]['plain_text']                        if item['properties']['Name']['title']                 else None ,
          'type':              item['properties']['Тип']['select']['name']                                                                                                  ,
          'date':              item['properties']['Дата']['date']['start']                                 if item['properties']['Дата']['date']                  else None ,
          'amount':            item['properties']['Сума']['number']                                                                                                         ,
          'status':            item['properties']['Статус']['select']['name']                              if item['properties']['Статус']                        else None ,
          'note':              item['properties']['Бележка']['rich_text'][0]['plain_text']                 if item['properties']['Бележка']['rich_text']          else None ,
          'year_id':           item['properties']['Година']['relation'][0]['id']                           if item['properties']['Година']['relation']            else None ,
          'month_id':          item['properties']['Месец']['relation'][0]['id']                            if item['properties']['Месец']['relation']             else None ,
          'category_id':       item['properties']['Категория']['rollup']['array'][0]['relation'][0]['id']  if item['properties']['Категория']['rollup']['array']  else None ,
          'subcategory_id':    item['properties']['Подкатегория']['relation'][0]['id']                     if item['properties']['Подкатегория']['relation']      else None ,
          'account_id':        item['properties']['Сметка']['rollup']['array'][0]['relation'][0]['id']     if item['properties']['Сметка']['rollup']['array']     else None ,
          'created_time':      item['created_time']                                                                                                                         ,
          'last_edited_time':  item['last_edited_time']                                                                                                                     
          }
        )

# Create pandas dataframe
df = pd.DataFrame(db_inc_exp_data)

# Load extracted data to the postgres database
df.to_sql(name='transaction', schema='01_src', con=engine, if_exists='delete_rows', index=False)

# print(df.iloc[13])

print(f"Loaded {len(inc_exp)} rows successfully!")