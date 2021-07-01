'''
Augments API Calls to return specifc reports for the BDFL
'''

import requests
import sys
import json
import time
from IPython.core.display import clear_output
import pandas as pd
import xml.etree.ElementTree as ET 
from tqdm import tqdm
tqdm.pandas()

class Reporter():
    '''
    This class contains functions that provide reports in the form of pandas dataframes
    It uses data from the myfantasyleague.com api
    '''

    def __init__(self, api, week):
        self.api = api
        self.week = week

    def jprint(self, obj):
        # dump formats the json in a pretty format
        text = json.dumps(obj, sort_keys=True, indent=4)
        print(text)


    def top_performers(self, count=3, week=None):
        '''
        Returns dataframe of the top COUNT performing players
        '''
        pscores_df = self.api.playerScores(COUNT = count, weeknum = week, df=True)
        # Add player name to the dataframes
        pscores_df = self.add_player_info(pscores_df, id_field = 'id')

        return pscores_df

    def ir_violations(self):
        '''
        Returns dataframe of IR Violations in the current week
        NOTE: Since we cannot currently see past status of players we cannot find ir_violations from past weeks
        '''
        franchise_players = self.api.rosters(df = True)
        # only observe those players on IR
        franchise_players = franchise_players[franchise_players['player_status'] == 'INJURED_RESERVE']
        # add score data
        franchise_players = self.add_player_scores(franchise_players, id_field = 'player_id')
        # only observe those players that scored points (violations)
        franchise_players['score'] = franchise_players['score'].replace('', 0)
        franchise_players = franchise_players[franchise_players['score'].astype(float) > 0]
        # adds player info columnsd to the dataframe
        franchise_players = self.add_player_info(franchise_players, id_field = 'player_id')
        return franchise_players

    def roster_report(self, team_id=None):
        '''
        returns a dataframe of all players owned in the league with 
        '''
        franchise_players = self.api.rosters(df = True)
        franchise_players = self.add_player_info(franchise_players, id_field = 'player_id')
        franchise_players = self.add_franchise_info(franchise_players, id_field = 'id_franchise')
        franchise_players = self.add_player_scores(franchise_players, id_field = 'player_id', week='YTD')
        franchise_players = franchise_players.drop(['week', 'status', 'player_id', 'isAvailable', 'id', 'id_score'], axis = 1)
        franchise_players.loc[:,'score'] = franchise_players['score'].astype(float)
        return franchise_players
        

    def get_adp_df(self):
        '''
        returns a dataframe with ADP information for each player in keeper leagues this year
        '''
        response = self.api.adp(PERIOD='ALL', FCOUNT='12', IS_PPR='-1', IS_KEEPER='K', IS_MOCK='-1', CUTOFF= 10, df= False)
        df = pd.DataFrame.from_dict(response['adp']['player'])
        df['averagePick'] = df['averagePick'].astype(float).round().astype(int)
        return df

    def add_franchise_info(self, df, id_field = 'id'):
        '''
        add's franchise name to the dataframe df
        '''
        # add franchise info
        league_info = self.api.league(df=True)
        # merge in franchise info
        df = df.merge(league_info[['id', 'name']], left_on = id_field, right_on = 'id', suffixes = ['_player', '_franchise'])
        return df
    
    def add_player_info(self, df, id_field = 'id'):
        '''
        adds player name, position and team to the dataframe df
        '''
        id_str = self.comma_str_from_series(df[id_field])
        info_df =  self.api.players(players=id_str, df=True)
        df = pd.merge(df, info_df, how = 'left', left_on = id_field, right_on = 'id', suffixes=('_franchise', '_player'))
        return df

    def add_player_scores(self, df, id_field = 'id', week=None):
        ''' 
        adds player score information based on the week to the df passed
        '''
        id_str = self.comma_str_from_series(df[id_field])
        score_df = self.api.playerScores(players=id_str, df=True, weeknum=week)
        df = pd.merge(df, score_df, how = 'left', left_on = id_field, right_on = 'id', suffixes=('', '_score'))
        return df
        
    def comma_str_from_series(self, series):
        '''
        accepts a series and returns the elements of that series sepereated by commas
        '''
        id_list = series.to_list()
        id_str = ','.join(id_list)
        return id_str
