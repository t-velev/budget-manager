import requests
import json
import os
import time

database_id = os.getenv('NOTION_INC_EXP_DB_ID')
api_key = os.getenv('NOTION_API_KEY')

headers = {
    'Authorization' : 'Bearer ' + api_key,
    'Content-type' : 'application/json',
    'Notion-Version' : '2022-06-28'
}

def get_inc_exp():
    """
    Extracts data from Notion "Income and Expenses" database and writes it to a JSON file.
    The function will be modified after a Postgres database is created.
    """
    
    url = f'https://api.notion.com/v1/databases/{database_id}/query'
    
    # Pagination variables to extract all rows (API size limit = 100)
    all_data = []
    has_more = True
    next_cursor = None

    # Loop through all pages
    while has_more:
        payload  = {'page_size' : 100}

        if next_cursor:
                payload['start_cursor'] = next_cursor

        response = requests.post(url, json=payload, headers=headers)

        data = response.json()

        all_data.extend(data['results'])
        
        # Update pagination variables
        has_more = data['has_more']
        next_cursor = data['next_cursor']
        
        time.sleep(0.4)       

    # Write the result as file
    with open('./data/notion_inc_exp_extract.json', 'w', encoding='utf-8') as file:
        json.dump(all_data, file, ensure_ascii=False, indent=4)

# inc_exp = get_inc_exp()
# print(f'Retrieved {len(inc_exp)} rows.') 

def read_file():
    """
    Reads the extracted "Income and Expenses" data from the JSON file and finds the needed elements
    that will be loaded in the Postgres database.
    The function will be modified after the Postgres database is created.
    """

    with open('data/notion_inc_exp_extract.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    cols = {}

    for i, item in enumerate(data):

        cols[i] = {
            'Id': item['id'],
            'Title': item['properties']['Name']['title'][0]['plain_text'],
            'Created_time': item['created_time'],
            'Last_edited_time': item['last_edited_time'],
        }

    return cols
    
cols = read_file()

print(cols)