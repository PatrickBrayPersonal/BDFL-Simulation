import pandas as pd
import numpy as np
import re


class Data_Generator():
    '''
    This class generates the basic data structures needed to execute the simulation
    '''

    def __init__(self, week, api, rep, pos_list, team_id_dict):
        self.week = week
        self.api = api
        self.rep = rep
        # TODO: make lib work
        self.pos_list = pos_list
        self.team_id_dict = team_id_dict
        self.plr_proj_dict = self.create_plr_proj_dict()
        self.sched_dict = self.create_sched_dict()
        self.pos_opp_dict = self.create_pos_opp_dict()
        self.score_df = self.create_score_df()

    def create_plr_proj_dict(self):
        '''
        generates the player mean score dictionary
        uses expert projections from fantasypros.com
        '''
        df_list = [None]*len(self.pos_list)
        for i, pos in enumerate(self.pos_list):
            df = pd.read_csv('../data/Season Projections/20210707/FantasyPros_Fantasy_Football_Projections_' + pos + '.csv')
            # TODO Print last modified date
            df = df[['Player', 'FPTS']]
            df = df.iloc[1:]
            df_list[i] = df
        df = pd.concat(df_list)
        # remove null values
        df = df[~pd.isna(df['Player'])]
        df['norm_player'] = df.Player.apply(self.normalize_name)
        df.index = df.norm_player
        del df['Player']
        plr_proj_dict = df.to_dict()['FPTS']
        assert plr_proj_dict['zachwilson'] == 246.2
        return plr_proj_dict

    def create_sched_dict(self):
        '''
        generates a dicitonary providing a week, team and opponent
        No teams are included when they are on bye
        '''
        a = self.api.nflSchedule()
        # CREATE DICTIONARY
        week_list = a['fullNflSchedule']['nflSchedule']
        sched_dict = {}
        for week, d in enumerate(week_list[0:18]):
            match_list = d['matchup']
            sched_dict[week] = {match['team'][0]['id']: match['team'][1]['id']
                                for match in match_list}
            # Add reverse matchups
            sched_dict[week] = {**sched_dict[week], **{match['team'][1]['id']: match['team'][0]['id']
                                                       for match in match_list}}
        return sched_dict

    def create_pos_opp_dict(self):
        '''
        generates the opponent-postion normalized dictionary
        data collected from https://www.fftoday.com/stats/fantasystats.php?Season=2020&GameWeek=Season&PosID=10&Side=Allowe
        '''
        df_list = [None]*len(self.pos_list)
        for i, pos in enumerate(self.pos_list):
            df = pd.read_excel('../data/Defensive Performance/2020/sportsref_download_' + pos + '.xlsx')
            # TODO Print last modified date
            df.rename(columns={'Unnamed: 0': 'Team',
                               'Fantasy per Game': 'PPG'},
                      inplace=True)
            df = df[['Team', 'PPG']]
            df = df.iloc[1:]
            df = df.append(pd.DataFrame({'Team': ['BYE'], 'PPG': [0]}))
            df['Pos'] = pos
            df_list[i] = df
        df = pd.concat(df_list)
        df.PPG = df.PPG.astype(float)
        df.Team = df.Team.map(self.team_id_dict)
        df['AVG_PPG'] = df.groupby(by=['Pos']).transform('mean') * 33/32  # account for bye week affecting mean
        df['PPG'] = df.PPG / df.AVG_PPG
        pos_opp_dict = df.groupby('Pos')[['Team','PPG']]\
                      .apply(lambda x: x.set_index('Team').to_dict(orient='index'))\
                      .to_dict()

        assert pos_opp_dict['QB']['NYJ']['PPG'] == 1.1905969896837476,\
            'Position dict generation, Jets defense estimated to be ' + str(pos_opp_dict['QB']['NYJ']['PPG'])
        return pos_opp_dict

    def read_sched_dict(self, x):
        '''
        reads the schedule dictionary for populating roster dataframe with matchups
        '''
        try:
            return self.sched_dict[x['week']-1][x['team']]
        except:
            return 'BYE'

    def mean_pts(self, x):
        '''
        returns the mean points expected for a player on a given week
        used in apply function x is row of dataframe
        '''
        try:
            return self.plr_proj_dict[x['norm_name_player']]/x['weeks_remaining'] *\
                    self.pos_opp_dict[x['position']][x['opp']]['PPG']
        except:
            return 0

    def create_score_df(self):
        '''
        returns the mean scores for each player in the BDFL
        '''
        roster_df = self.rep.roster_report()
        # Repeat dataframe rows and add week numbers remaining
        roster_df = pd.DataFrame(np.repeat(roster_df.values, 19-self.week, axis=0), columns=roster_df.columns)
        roster_df['week'] = list(range(self.week, 19)) * len(roster_df.drop_duplicates('player_id'))
        roster_df['opp'] = roster_df.apply(lambda x: self.read_sched_dict(x), axis=1)
        roster_df['weeks_remaining'] = roster_df.week.max() - self.week + 1
        roster_df.name_player = roster_df.name_player.str.split(', ').map(lambda x: ' '.join(x[::-1]))
        # Create normalized player name id
        roster_df['norm_name_player'] = roster_df.name_player.apply(self.normalize_name)
        # roster_df
        roster_df['mean_pts'] = roster_df.apply(lambda x: self.mean_pts(x), axis=1)
        self.roster_df = roster_df
        return roster_df
        # roster_df['']

    def normalize_name(self, name):
        name = ''.join(name.lower().split()[0:2])
        regex = re.compile('[^a-z]')
        name = regex.sub('', name)
        return name




# roster_df['mean_score'] = 
                                   


