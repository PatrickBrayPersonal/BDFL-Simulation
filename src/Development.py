
'''
# import requests
# import sys
# import json
# import time
import requests_cache
# from IPython.core.display import clear_output
# 1import xml.etree.ElementTree as ET
# from tqdm import tqdm
# tqdm.pandas()
# import lib
from API_Wrapper import API
from Reporter import Reporter
from Data_Generator import Data_Generator
from Simulator import Simulator

# this function call will transparent cache new API requests, and use the cahce whenever we make a repeated call
requests_cache.install_cache()

# Global Variables
LEAGUE_ID = '65522'
USER_AGENT = 'brayps_user_agent'

pos_list = ['QB', 'RB', 'WR', 'TE']
team_id_dict = {'Arizona Cardinals': 'ARI',
                'Atlanta Falcons': 'ATL',
                'Baltimore Ravens': 'BAL',
                'Buffalo Bills': 'BUF',
                'Carolina Panthers': 'CAR',
                'Chicago Bears': 'CHI',
                'Cincinnati Bengals': 'CIN',
                'Cleveland Browns': 'CLE',
                'Dallas Cowboys': 'DAL',
                'Denver Broncos': 'DEN',
                'Detroit Lions': 'DET',
                'Green Bay Packers': 'GBP',
                'Houston Texans': 'HOU',
                'Indianapolis Colts': 'IND',
                'Jacksonville Jaguars': 'JAC',
                'Kansas City Chiefs': 'KCC',
                'Las Vegas Raiders': 'LVR',
                'Los Angeles Chargers': 'LAC',
                'Los Angeles Rams': 'LAR',
                'Miami Dolphins': 'MIA',
                'Minnesota Vikings': 'MIN',
                'New England Patriots': 'NEP',
                'New Orleans Saints': 'NOS',
                'New York Giants': 'NYG',
                'New York Jets': 'NYJ',
                'Philadelphia Eagles': 'PHI',
                'Pittsburgh Steelers': 'PIT',
                'San Francisco 49ers': 'SFO',
                'Seattle Seahawks': 'SEA',
                'Tampa Bay Buccaneers': 'TBB',
                'Tennessee Titans': 'TEN',
                'Washington Football Team': 'WAS',
                'BYE': 'BYE'
                }
week = 1
n = 10
# Instatiate Classes
api = API(leagueid=LEAGUE_ID, user_agent=USER_AGENT)
rep = Reporter(api=api, week=1)
dg = Data_Generator(1, api, rep, pos_list, team_id_dict, n)
sim = Simulator(week, api,' rep, dg, n)'''



import warnings
warnings.filterwarnings('ignore')
from IPython.display import Image
from API_Wrapper import API
from Reporter import Reporter
from Data_Generator import Data_Generator
from Simulator import Simulator
# Creds
LEAGUE_ID = '65522'
USER_AGENT = 'brayps_user_agent'
# Current week of the season
week = 1
# Number of seasons to run
n = 20
assert n >= 10
# Instatiate Classes
api = API(leagueid=LEAGUE_ID, user_agent=USER_AGENT)
rep = Reporter(api, week)
dg = Data_Generator(week, api, rep, n)
sim = Simulator(week, api, rep, dg, n)



# import numpy as np
cov_mat = np.array([[1, 1.5],[-1, 1]])
means = [0, 1]
rand_vars = np.random.multivariate_normal(means, cov_mat, size=10000)
