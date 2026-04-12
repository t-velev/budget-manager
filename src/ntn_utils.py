import requests
import json
import os
import time
import pandas as pd
from sqlalchemy import text
from datetime import datetime
from zoneinfo import ZoneInfo

api_key = os.getenv('NOTION_API_KEY')

def get_data(db_id: str, last_load_date: datetime, filter_cols: list) -> list[dict]:
    """
    Extract data from specific database in Notion.

    Since Notion API has request size limit of 100 rows,
    the function uses pagination variables to make multiple
    API calls untill all the data is extracted.

    Returns:
        list[dict]: A list with all rows in dictionary form.
    """

    headers = {
        'Authorization' : 'Bearer ' + api_key,
        'Content-type' : 'application/json',
        'Notion-Version' : '2022-06-28'
        }

    filter_string = ''

    if filter_cols:

        # Building a string of filters to be added to url
        for col in filter_cols:

            if col == filter_cols[0]:
                filter_string = '?filter_properties[]=' + col
            else:
                filter_string = filter_string + '&filter_properties[]=' + col

        url = f'https://api.notion.com/v1/databases/{db_id}/query' + filter_string

    else:
        url = f'https://api.notion.com/v1/databases/{db_id}/query'

    # Pagination variables to extract all rows
    all_data = []
    has_more = True
    next_cursor = None

    # Loop through all pages
    while has_more == True: # and len(all_data) < 50:  # Capped at 50 during development

        payload = {'page_size' : 100}                # Notion API request size limit = 100

        # Empty list to hold filters
        filter_list = []

        # Add incremental filter if it exists
        if last_load_date:

            last_load_date_local = last_load_date.replace(tzinfo=ZoneInfo("Europe/Sofia"))    # Add local timezone
            last_load_date_utc = last_load_date_local.astimezone(ZoneInfo("UTC"))             # Convert to UTC
            last_load_date_tz = last_load_date_utc.isoformat()                                # Convert to string so it can be used in the json payload

            filter_list.append({'timestamp': 'last_edited_time',
                                'last_edited_time': {'after': last_load_date_tz}
                               })

        # Extract transactions not used as template or with status Предстои.
        # They have missing values and aren't used as a typical transaction.
        if db_id == os.getenv('NOTION_DB_ID_TRANSACTION'):

            filter_list.append({
                                'and': [
                                        {'property': 'Template' ,
                                         'checkbox': {'does_not_equal': True} 
                                        } ,
                                        {'property': 'Статус' ,
                                         'select'  : {'does_not_equal': 'Предстои'}
                                        }
                                       ]
                                })
            
        # Finalize the filters payload
        if filter_list:
            payload['filter'] = {'and': filter_list}

        # Set to continue with the next batch of records if there are such
        if next_cursor:
            payload['start_cursor'] = next_cursor

        # Make an API post request
        response = requests.post(url, json=payload, headers=headers)

        data = response.json()

        all_data.extend(data['results'])

        # Update pagination variables
        has_more = data['has_more']
        next_cursor = data['next_cursor']

        # Pause to not overload the API (Rate limit = 3 req/sec)
        time.sleep(0.5)

    # Write the result as file - For dev phase
    # with open('./data/notion_transaction_full.json', 'w', encoding='utf-8') as file:
    #     json.dump(all_data, file, ensure_ascii=False, indent=4)           

    return all_data


def get_last_load_date(schema: str, table_name: str, engine) -> datetime:
    """
    Extract the maximum value of column LOAD_DATE from budget_manager_dwh database.

    Returns:
        datetime: A datetime/timestamp value.
    """

    # Get the last load date from the database
    query = f'select max(load_date) from {schema}.{table_name}'
    df = pd.read_sql_query(query, engine)

    last_load_date = df.iloc[0].item()

    return last_load_date


def load_new_data(schema_name: str, table_name: str, new_data_df, engine):
    """
    Load data into a selected budget_manager_dwh database table.

    Returns:
    """

    with engine.begin() as conn:

        if len(new_data_df) > 0:

            ids_list = new_data_df['id'].tolist()

            # Delete and then insert the changed existing values by key instead of updating them.
            # Using a named parameter :id_list and passing the values in a dictionary,
            # because a tuple with one value has a trailing comma and it breaks a standard query statement
            query = text(f'DELETE from {schema_name}.{table_name} where id in :id_list')
            conn.execute(query, {'id_list': tuple(ids_list)})

            # Load extracted data to the postgres budget-db
            result = new_data_df.to_sql(name=table_name, con=conn, schema=schema_name, if_exists='append', index=False, method='multi', chunksize=1000)

            return result


def del_missing_data(schema_name: str, table_name: str, filtered_df, engine) -> int:
    """
    Delete rows in the target table which are missing (deleted) in the source.

    It does that by using a reference table raw.NOTION_IDS_AUDIT, loaded with
    the most current values of source ids just before the delete.

    Intentionally done in two separate db transactions.

    Returns:
        int: Return how many rows were actually deleted.
    """

    with engine.begin() as conn:

        # Delete the old data from previous runs
        query = text(f"DELETE from {schema_name}.notion_ids_audit where source_name = '{table_name}'")
        conn.execute(query)

        # Load the most current ids
        filtered_df.to_sql(name='notion_ids_audit', con=conn, schema=schema_name, if_exists='append', index=False, method='multi', chunksize=1000)

        # Use the ids in NOTION_IDS_AUDIT to find and delete the missing rows
        query = text(f"DELETE from {schema_name}.{table_name} t where not exists (select 1 from {schema_name}.notion_ids_audit tt where tt.id = t.id and tt.source_name = '{table_name}')")
        result = conn.execute(query)

        return result.rowcount # Return how many rows were actually deleted