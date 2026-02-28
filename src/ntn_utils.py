import requests
import json
import os
import time

api_key = os.getenv('NOTION_API_KEY')

def get_data(db_id: str) -> list[dict]:
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

    url = f'https://api.notion.com/v1/databases/{db_id}/query'
    
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