# finalproject_SI507

REQUIRED PACKAGES (shown via import statements in code):__
import requests
import time
import hashlib
import json
from bs4 import BeautifulSoup
import sqlite3
import plotly.graph_objects as go


SPECIAL INSTRUCTIONS:
If the marvel_characters.db file does not exist and the program is being run for the first time then only the below two functions should be run. Currently 
these functions are commented out in the code to avoid running these functions by default.
-create_database_table() - this function will newly create two tables in the .db file. If this funciton is run repeatedly then it will overwrite the 
                           data input on each run into the database. As such ** only run this function if the marvel_characters.db file does not exist

-populate_database() - this function will populate the database with all the data in the caching json file. This funciton should also only be run once, after all 
                       the data has been scraped from the marvel website. Running this function repeatedly will keep adding redundant data into the database.
                       
In order to run the program, no additional information is required. 
I am using an API to extract information about the events that various Marvel characters have been present in. This API requires four parameters to run: 
-'apikey'
-'ts' - this is the timestamp
-'hash' - a hash value created from the md5 hash function. In order to obtain the appropriate hash value for the API to work the timestamp + private api key 
          + public api key must be passed into the hash function. 
-'name' - name of marvel character

All four of these parameters have been calcualted in the finalproject.py script within the get_event_info() function and no further action is required.
                       
                       
                       
HOW TO INTERACT WITH PROGRAM:
Interacting with the program is very simple. The program will ask the user to enter the name of a Marvel character. If the Marvel character is found in the database
then the program will return a console summary of the character that includes its name, link to character webpage, powers, and events the character was present 
in. In addition, the program will also create a bar plot for the character that summarizes the powers of the character. This way the program allows an easy way 
to compare the powers of each Marvel character as the user can scroll through the various tabs for each Marvel character. If the marvel character is not found 
in the database, or if the entry is invalid then the proram will ignore the entry and ask for another input. If the user types in "exit" the program will thank
the user and exit. 
