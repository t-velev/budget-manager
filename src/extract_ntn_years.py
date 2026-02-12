import requests
import json
import os

database_id = os.getenv('NOTION_YEARS_DB_ID')
api_key = os.getenv('NOTION_API_KEY')

headers = {
    'Authorization' : 'Bearer ' + api_key,
    'Content-type' : 'application/json',
    'Notion-Version' : '2022-06-28'
}

def get_years():
    """
    Extracts data from Notion "Years" database and writes it to a JSON file.
    The function will be modified after a Postgres database is created.
    """
    
    url = f'https://api.notion.com/v1/databases/{database_id}/query'
    
    #payload  = {'page_size' : 10}
    response = requests.post(url, headers=headers)

    data = response.json()

    # Writes the result as file
    with open('./data/notion_years_extract.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# get_years()

def read_file():
    """
    Reads the extracted "Years" data from the JSON file and finds the needed elements
    that will be loaded in the Postgres database.
    The function will be modified after the Postgres database is created.
    """

    with open('data/notion_years_extract.json', 'r', encoding = 'utf-8') as file:
        data = json.load(file)

    cols = {}

    for i, item in enumerate(data['results']):

        cols[i] = {
            'Id': item['id'],
            'Title': item['properties']['Име']['title'][0]['plain_text'],
            'Created_time': item['created_time'],
            'Last_edited_time': item['last_edited_time'],
        }

    return cols
    
cols = read_file()

print(cols)