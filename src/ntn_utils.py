import requests
import json
import os
import time
import pandas as pd
from sqlalchemy import Table, Column, Integer, String, Date, MetaData, select, insert, update, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from zoneinfo import ZoneInfo


def get_data(db_id: str, last_load_date: datetime, filter_cols: list) -> list[dict]:
    """
    Extract data from specific Notion database.

    Since Notion API has request size limit of 100 rows,
    the function uses pagination variables to make multiple
    API calls untill all data is extracted.

    Args:
        db_id (str): The Notion database id, from which data will be extracted.
        last_load_date (datetime): The date and the time when the last data load was done.
        filter_cols (list): A list of column names to be filtered and extracted from the Notion database.

    Returns:
        list[dict]: A list with all rows in dictionary form.
    """

    api_key = os.getenv('NOTION_API_KEY')

    headers = {
        'Authorization' : 'Bearer ' + api_key,
        'Content-type' : 'application/json',
        'Notion-Version' : '2022-06-28'
        }

    # Building a string of filters (with column names) to be added to the url
    filter_string = ''

    if filter_cols:
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

        # If it's the heavy subcategory table, only ask for 25 rows at a time to prevent Notion 504 timeouts.
        # Otherwise, use the max 100.
        if db_id == os.getenv('NOTION_DB_ID_SUBCATEGORY'):
            payload = {'page_size': 25}
        else:
            payload = {'page_size': 100}      # Notion API request size limit = 100

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

        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Make an API post request
                response = requests.post(url, json=payload, headers=headers, timeout=90)

                # Raise exception if Notion's API returns status <> success
                response.raise_for_status()

            # Catch API HTTP errors (rate_limited, bad_gateway, unauthorized)
            except requests.exceptions.HTTPError as e:

                # Check for 429 (Rate Limit) or 504 (Timeout) error
                if response.status_code in [429, 504]:
                    if attempt < max_retries - 1:
                        print(f'Notion is busy (Status {response.status_code}). Waiting 20 seconds...')
                        time.sleep(20)
                        continue  # Try again
                    else:
                        print(f'Max retries reached. Failing script due to API timeout.')
                        raise e
                else:
                    print(f'Fatal API Error: {response.status_code}. Stopping script.')
                    raise e

            # Catch basic connection errors (no internet, DNS failure)
            except requests.exceptions.RequestException as e:

                if attempt < max_retries - 1:
                    print(f'Network error: {e}. Waiting 20 seconds...')
                    time.sleep(20)
                    continue
                else:
                    print(f'Max retries reached for Network Error. Failing script.')
                    raise e       # Crash the script

            else:
                # If try block succeed:
                # Format response into json and add to list
                data = response.json()
                all_data.extend(data['results'])

                # Update pagination variables
                has_more = data['has_more']
                next_cursor = data['next_cursor']

                # Pause to not overload the API (Rate limit = 3 req/sec)
                time.sleep(0.5)

                # Break out of the retry loop when succeed
                break

    return all_data


def get_last_load_date(schema_name: str, table_name: str, engine) -> datetime:
    """
    Extract the maximum value of column LOAD_DATE from budget_manager_dwh database.

    Args:
        schema_name (str): The name of the target schema for the data load.
        table_name (str): The name of the target table for the data load.
        engine: The database connection object.

    Returns:
        datetime: The date and the time when the last data load was done.
    """

    # Get the last load date from the database
    query = f'select max(load_date) from {schema_name}.{table_name}'

    try:
        df = pd.read_sql_query(query, engine)

    except (pd.errors.DatabaseError, SQLAlchemyError) as e:
        print(f'Error: Could not query {schema_name}.{table_name}. Details: {e}')
        raise

    last_load_date = df.iloc[0].item()

    if last_load_date is None:
        print(f'No previous loads found in {table_name}.{schema_name}. Preparing for full load.')
    else:
        print(f'Last load date = {last_load_date}. Preparing for incremental load.')

    return last_load_date


def load_new_data(schema_name: str, table_name: str, new_data_df, engine) -> int:
    """
    Load new/incremental data into a budget_manager_dwh database table.

    Args:
        schema_name (str): The name of the target schema for the data load.
        table_name (str): The name of the target table for the data load.
        new_data_df (df): Dataframe of the new data that will be loaded.
        engine: The database connection object.

    Returns:
        int: The number of rows affected.
    """

    try:
        with engine.begin() as conn:

            if len(new_data_df) > 0:

                # Transform the Notion IDs to a list
                ids_list = new_data_df['id'].tolist()

                # DELETE records from the raw table by using new records IDs if they are already there
                query = text(f'DELETE from {schema_name}.{table_name} where id in :id_list')

                # Execute the DELETE using a named parameter :id_list and passing the values in a dictionary,
                # because a tuple with one value has a trailing comma and it breaks a standard query statement.
                conn.execute(query, {'id_list': tuple(ids_list)})

                # INSERT the new records to the raw table
                result = new_data_df.to_sql(name=table_name, con=conn, schema=schema_name, if_exists='append', index=False, method='multi', chunksize=1000)

            else:
                result = 0

            return result

    except (pd.errors.DatabaseError, SQLAlchemyError) as e:
        print(f'Error: The load new data process failed for {schema_name}.{table_name}. Details: {e}')
        raise


def del_missing_data(schema_name: str, table_name: str, filtered_df, engine) -> int:
    """
    Delete rows in the target table which are missing (deleted) in the source.

    It does that by using a reference table raw.NOTION_IDS_AUDIT, loaded with
    the most current values of source ids just before the delete.

    Intentionally done in two separate db transactions.

    Args:
        schema_name (str): The name of the target schema for the data load.
        table_name (str): The name of the target table for the data load.
        filtered_df (df): Dataframe of the filtered data that will be loaded.
        engine: The database connection object.

    Returns:
        int: How many rows were actually deleted.
    """

    try:
        with engine.begin() as conn:

            # DELETE the ID records from previous runs so we can insert the most current ones
            query = text(f"DELETE from {schema_name}.notion_ids_audit where source_name = '{table_name}'")
            conn.execute(query)

            # INSERT the most current IDs into notion_ids_audit table
            filtered_df.to_sql(name='notion_ids_audit', con=conn, schema=schema_name, if_exists='append', index=False, method='multi', chunksize=1000)

            # Use the IDs in NOTION_IDS_AUDIT to find and DELETE the missing rows
            query = text(f"DELETE from {schema_name}.{table_name} t where not exists (select 1 from {schema_name}.notion_ids_audit tt where tt.id = t.id and tt.source_name = '{table_name}')")
            result = conn.execute(query)

            return result.rowcount # Return how many rows were actually deleted

    except (pd.errors.DatabaseError, SQLAlchemyError) as e:
        print(f'Error: The delete missing data process failed for {schema_name}.{table_name}. Details: {e}')
        raise


def upsert_into_stats(engine, row_count: int, run_id: int, run_date: datetime, dag_name: str, task_name: str, column: str) -> None:
    """
    Insert or update the values in the sys_etl_stats log table for the current dag run.

    Check if a row exists for the current run_id. If not, create one. Else, update values.

    Args:
        engine: The database connection object.
        row_count (int): The number of rows that are extracted from Notion through get_new_data().
        run_id (int): The current dag run's id. Integer corresponding to YYYYMMDDHHMISS format.
        run_date (datetime): The current date and time when the script was executed. The time is localized to Europe/Sofia.
        dag_name (str): The name of the Airflow dag.
        task_name (str): The name of the Airflow task.
        column (str): The name of the column in sys_etl_stats to be filled.

    Returns:
        None
    """

    metadata = MetaData()

    # Define table object
    stats_table = Table(
        "sys_etl_stats",
        metadata,
        Column("run_id"        , Integer),
        Column("run_date"      , Date   ),
        Column("dag_name"      , String ),
        Column("task_name"     , String ),
        Column("ntn_extracted" , Integer),
        Column("raw_loaded"    , Integer),
        Column("raw_deleted"   , Integer),
        Column("wh_loaded"     , Integer),
        Column("wh_closed"     , Integer),
        schema="warehouse"
    )

    try:
        with engine.begin() as conn:

            # Check if a row with the current dag run_id, name and task exists
            select_stmt = select(stats_table).where( stats_table.c.run_id    == run_id,
                                                     stats_table.c.dag_name  == dag_name,
                                                     stats_table.c.task_name == task_name
                                                     )
            select_result = conn.execute(select_stmt).fetchone()

            # If no row exists, create one. Else, update the values
            if not select_result:
                insert_stmt = ( insert(stats_table)
                               .values({ stats_table.c.run_id:    run_id,
                                         stats_table.c.run_date:  run_date,
                                         stats_table.c.dag_name:  dag_name,
                                         stats_table.c.task_name: task_name,
                                         stats_table.c[column]:   row_count
                                       })
                               )
                insert_result = conn.execute(insert_stmt)
            else:
                update_stmt = ( update(stats_table)
                               .where( stats_table.c.run_id    == run_id,
                                       stats_table.c.run_date  == run_date,
                                       stats_table.c.dag_name  == dag_name,
                                       stats_table.c.task_name == task_name)
                               .values({ stats_table.c[column]: row_count })
                               )
                update_result = conn.execute(update_stmt)

    except SQLAlchemyError as e:
        print(f'Error: Could not upsert stats for {task_name}. Details: {e}')
        raise