'''
Mimic Reporter.py
'''
import requests
import sys
import json
import time
import requests_cache
from IPython.core.display import clear_output
import pandas as pd
import xml.etree.ElementTree as ET 
from tqdm import tqdm
tqdm.pandas()


from API_Wrapper import API
from Reporter import Reporter

# this function call will transparent cache new API requests, and use the cahce whenever we make a repeated call
requests_cache.install_cache()

# Global Variables
LEAGUE_ID = '65522'
USER_AGENT = 'brayps_user_agent'

# Instatiate Classes
api = API(leagueid=LEAGUE_ID, user_agent=USER_AGENT)
rep = Reporter(api = api, week = '15')

print(api.allRules())