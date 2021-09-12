import requests
import time
import hashlib
import json
from bs4 import BeautifulSoup
import sqlite3
import plotly.graph_objects as go

DBNAME = 'marvel_characters.db'
connection = sqlite3.connect(DBNAME)
cursor = connection.cursor()

CACHE_FILENAME_CHARACTERS = "characters_cache.json"

def open_cache(cache_filename):
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(cache_filename, 'r')
        cache_contents = cache_file.read()
        CACHE_DICT = json.loads(cache_contents)
        cache_file.close()
    except:
        CACHE_DICT = {}
    return CACHE_DICT

def save_cache(cache_dict, cache_filename):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''

    dumped_json_cache = json.dumps(cache_dict, sort_keys=True, indent=0)
    fw = open(cache_filename,"w")
    fw.write(dumped_json_cache)
    fw.close()

def get_event_info(character_name):

    base_url_api = "http://gateway.marvel.com/v1/public/characters"
    api_key_public = "47afdd489562831d49d7ee079fedbc69"
    api_key_private = "8735fd6c7c994d79c2b990c348454dfbbb668fcd"
    ts = str(time.time())[0:10]

    hashstring = bytes(ts + api_key_private + api_key_public, encoding='utf-8')
    hash_result = hashlib.md5(hashstring)
    hash_result_digest = hash_result.hexdigest()

    params = {
        'apikey': api_key_public,
        'ts': ts,
        'hash': hash_result_digest,
        'name': character_name
    }

    response = requests.get(base_url_api, params)

    response_json = response.json()
    response_results_events = response_json['data']['results']

    #print(response_results[0]['events']['items'])

    return response_results_events



#Beautiful soup to scrape webpage: 

def extract_characters():

    offset = 0
    limit = 10
    response_item_list = []
    character_dict = {}
    base_url = 'https://www.marvel.com'

    character_dict = open_cache(CACHE_FILENAME_CHARACTERS)
    if not character_dict:
        for character_counts in range(0, 360, 36):
            print("working....", offset)
            base_url_characters = f'https://www.marvel.com/v1/pagination/grid_cards?offset={offset}&limit={limit}&entityType=character&sortField=title&sortDirection=asc'
            response = requests.get(base_url_characters)
            response_json = response.json()
            for item in response_json['data']['results']['data']:
                character_title = item['link']['title']
                character_info_link = item['link']['link']
                character_dict[character_title] = {}
                character_dict[character_title]['link'] = base_url+character_info_link
                character_dict[character_title]['powers'] = {}
                character_dict[character_title]['events'] = [0]
            if character_counts != 2592:
                offset += 36
            save_cache(character_dict, CACHE_FILENAME_CHARACTERS)

    return character_dict


def extract_character_info():

    character_dict = extract_characters()

    for key in character_dict.keys():
        if character_dict[key]['powers'] == {}:
            print(f"working on character power extraction...{key} ")
            character_link = character_dict[key]['link']
            response = requests.get(character_link)
            soup = check_for_power_page(response)
            power_numbers_div = soup.find_all("div", class_="power-grid grid-wrapper--nested")
            power_numbers_span = power_numbers_div[0].find_all("span")
            power_items = soup.find_all("div", class_="power-circle__label")
            if power_items:
                power_dict = {}
                for i, power in enumerate(power_items):
                    power_name = power.contents[0]
                    power_value = power_numbers_span[i].contents[0]
                    power_dict[power_name] = power_value

                character_dict[key]['powers'] = power_dict
            else:
                character_dict[key]['powers'] = "powers not listed"
        save_cache(character_dict, CACHE_FILENAME_CHARACTERS)

    return character_dict


def check_for_power_page(response_object):

    base_url = 'https://www.marvel.com'

    soup = BeautifulSoup(response_object.text, 'html.parser')
    power_numbers_div = soup.find_all("nav", class_="masthead__tabs")
    if power_numbers_div:
        ordered_list_items = power_numbers_div[0].find_all("li", class_="masthead__tabs__li")
        anchor_tag_comics_report = ordered_list_items[-1].find("a", href=True)
        character_link = base_url + anchor_tag_comics_report['href']
        print(character_link)
        response = requests.get(character_link)
        soup = BeautifulSoup(response.text, 'html.parser')
        print("This page has tabs. Extracting power page by navigating to the relevant tab.")
    else:
        print("Nothing relevant present in masthead__tabs class in webpage. This page likely doesn't have tabs.")

    return soup




def dbconn(query):
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    connection.close()
    return result


class Character:
    def __init__(self, name, info_link, powers, events):
        self.name = name
        self.info_link = info_link
        self.powers = powers

        if events != [[]] or []:
            self.events = events['items']
        else:
            self.events = "This character is not mentioned in any events"

    def info(self):

        return f'''
        Name: {self.name}
        Character Information: {self.info_link}
        Powers: {self.powers}
        Events: {self.events}
        '''




character_dict = extract_character_info()
character_object_list = []
character_dict = open_cache(CACHE_FILENAME_CHARACTERS)


def create_database_table():

    q1 = '''CREATE TABLE "CharacterInfo" (
    "id"	INTEGER NOT NULL,
    "Name"	TEXT NOT NULL,
    "Link"	TEXT,
    "Durability"	INTEGER,
    "Energy"	INTEGER,
    "Fighting Skills"	INTEGER,
    "Intelligence"	INTEGER,
    "Speed"	INTEGER,
    "Strength"	INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT));'''

    cursor.execute(q1)


    q2 = '''CREATE TABLE "CharacterEvents" (
    "id"	INTEGER NOT NULL,
    "infoId"	INTEGER,
    "Events"	TEXT,
    PRIMARY KEY("id" AUTOINCREMENT),
    FOREIGN KEY("infoId") REFERENCES "CharacterInfo"("id"));'''

    cursor.execute(q2)


def populate_database():

    sql_info = "INSERT INTO CharacterInfo (`Name`, `Link`, `Durability`, `Energy`, `Fighting Skills`, `Intelligence`, `Speed`, `Strength`) VALUES (?,?,?,?,?,?,?,?)"
    sql_events = "INSERT INTO CharacterEvents (`infoId`, `Events`) VALUES (?,?)"

    events_list = []
    if character_dict[key]['powers'] != "powers not listed":
            val = (key, character_dict[key]['link'], character_dict[key]['powers']['durability'], character_dict[key]['powers']['energy'], character_dict[key]['powers']['fighting skills'], character_dict[key]['powers']['intelligence'], character_dict[key]['powers']['speed'], character_dict[key]['powers']['strength'])
    else:
        val = (key, character_dict[key]['link'], None, None, None, None, None, None)
    cursor.execute(sql_info, val)
    last_id = cursor.lastrowid

    if character_dict[key]['events'] != [[]]:
        for event_dict in character_dict[key]['events']['items']:
            if character_dict[key]['events']['items'] != []:
                val = event_dict["name"]
                events_list.append(val)
            else:
                val = None
                events_list.append(val)
    for item in events_list:
        cursor.execute(sql_events, (last_id,item))



def interactive_prompt():

    running = True
    while running:
        character_input = input("Please enter the name of a Marvel character: ")
        if character_input.lower() == 'exit':
            print("Thanks for using the Marvel Character Database!" + "\n")
            running = False
        else:
            character_input = character_input.title()
            character_input = character_input.replace("bar", "")

            for character in character_object_list:
                if character_input in character.name:
                    name_var = character.name
                    if "'" in name_var:
                        name_var = name_var.replace("'", "''")

                    query = f"select * from CharacterInfo where Name = '{name_var}'"
                    query_result = dbconn(query)
                    print(character.info())
                    if character.powers != "powers not listed":
                        x_list = list(character.powers.keys())
                        y_list = []
                        for power_str in character.powers.values():
                            power_int = int(power_str)
                            y_list.append(power_int)

                        bar_data = go.Bar(x=x_list, y=y_list)
                        basic_layout = go.Layout(title=f"{character.name}")
                        fig = go.Figure(data=bar_data, layout=basic_layout)
                        fig.show()
                else:
                    continue


#### Only run below function if running the script for the first time and the marvel_characters.db file does not exist in the directory ####
#create_database_table()

for x, key in enumerate(character_dict.keys()):
    character_dict = open_cache(CACHE_FILENAME_CHARACTERS)
    char_obj = Character(key, character_dict[key]['link'], character_dict[key]['powers'], character_dict[key]['events'])
    character_object_list.append(char_obj)

    if character_dict[key]['events'] == [0]:
        print("running....")
        result = get_event_info(key)
        if result != [] and result[0]['events'] not in character_dict[key].values():
            print('storing events....')
            character_dict[key]['events'] = result[0]['events']
            save_cache(character_dict, CACHE_FILENAME_CHARACTERS)
        else:
             character_dict[key]['events'] = []
             save_cache(character_dict, CACHE_FILENAME_CHARACTERS)


    #### Only run below function if running the script for the first time and the marvel_characters.db file does not exist in the directory ####
    # populate_database()



connection.commit()
cursor.close()
connection.close()


if __name__ == "__main__":
    interactive_prompt()

