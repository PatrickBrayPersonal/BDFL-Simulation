'''
Mimic Reporter.py
'''
# import requests
# import sys
# import json
# import time
import requests_cache
# from IPython.core.display import clear_output
import pandas as pd
# 1import xml.etree.ElementTree as ET
# from tqdm import tqdm
# tqdm.pandas()
# import lib
from API_Wrapper import API
from Reporter import Reporter
from Data_Generator import Data_Generator

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
# Instatiate Classes
api = API(leagueid=LEAGUE_ID, user_agent=USER_AGENT)
rep = Reporter(api=api, week=1)
# dg = Data_Generator(1, api, rep, pos_list, team_id_dict, n=10)

# dg.to_pickle('data/dg.pckl')
# api.to_pickle('data/api.pckl')
# rep.to_pickle('data/rep.pckl')
# dg.score_df.to_pickle('../data/score_df.pckl')

score_df = pd.read_pickle('../data/score_df.pckl')


# =============================================================================
# =============================================================================
# =============================================================================
# Simulate BDFL Season
# =============================================================================
n = 10
sched_list = api.leagueSched()['schedule']['weeklySchedule']
# TODO: Simulate the playoffs
# Simulate the bench players
weeks_rem = range(week, 14)
matchup_list = [None] * n * len(weeks_rem) * 6
for run in range(0, n):
    for week in weeks_rem:
        # print(sched_list[week - 1])
        for i, matchup in enumerate(sched_list[week - 1]['matchup']):
            id0 = matchup['franchise'][0]['id']
            id1 = matchup['franchise'][1]['id']
            # TODO: draw from sims not from mean
            team0_pts = score_df.loc[(score_df.week == week) &
                                     (score_df.id_franchise == id0) &
                                     (score_df['start']), 'mean_pts'].sum()
            team1_pts = score_df.loc[(score_df.week == week) &
                                     (score_df.id_franchise == id1) &
                                     (score_df['start']), 'mean_pts'].sum()
            # print(run, len(weeks_rem), week, i)
            mu_idx = run*len(weeks_rem)*6+(week-1)*6+i
            # print(mu_idx)
            matchup_list[mu_idx] = [run, week, id0, team0_pts, id1, team1_pts]
            # print(matchup_list[mu_idx])
matchup_df = pd.DataFrame(matchup_list, columns=['run', 'week', 'id0', 'team0_pts', 'id1', 'team1_pts'])
matchup_df.loc[matchup_df.team0_pts > matchup_df.team1_pts, 'winner'] = matchup_df.id0
# TODO: Allow for ties
matchup_df.winner = matchup_df.winner.fillna(matchup_df.id1)
