import pandas as pd
import numpy as np
import re
from numpy.random import multivariate_normal


class Data_Generator():
    '''
    This class generates the basic data structures needed to execute the simulation
    '''

    def __init__(self, week, api, rep, pos_list, team_id_dict, n=10):
        self.week = week
        self.api = api
        self.rep = rep
        # TODO: make lib work
        self.pos_list = pos_list
        self.team_id_dict = team_id_dict
        self.plr_proj_dict = self.create_plr_proj_dict()
        self.sched_dict = self.create_sched_dict()
        self.pos_opp_dict = self.create_pos_opp_dict()
        self.n = n
        self.mean_order = ['QB1', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE1']
        self.corrs = pd.read_excel('../data/Position_correlations.xlsx', sheet_name='RAW', index_col=0).to_numpy()
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
        # Add mean points
        roster_df['mean_pts'] = roster_df.apply(lambda x: self.mean_pts(x), axis=1)
        roster_df = self.add_position_rank(roster_df)
        # Simulate NFL games
        roster_df = self.add_random_pts(roster_df)
        return roster_df

    def gen_rand_pts(self, means):
        '''
        takes in an array of means scores for each player and outputs a 2d array of n simulations of the game
        '''
        # TODO; Covariance = Corr * SQRT(VAR(X)VAR(Y))
        cov_matrix = self.corrs
        # Anything that comes in as a 0 should leave as a 0
        data = multivariate_normal(means, cov_matrix, size=self.n)
        return data

    def normalize_name(self, name):
        name = ''.join(name.lower().split()[0:2])
        regex = re.compile('[^a-z]')
        name = regex.sub('', name)
        return name

    def clean_mean_list(self, ls):
        return [item[0] if len(item) > 0 else 0 for item in ls]

    def find_game_means(self, df, week, team, opp_team):
        team_mean_list = [df[(df.week == week) & (df.team == team) & (df.pos_rank == pos_rank)].mean_pts.values for pos_rank in self.mean_order]
        opp_mean_list = [df[(df.week == week) & (df.team == opp_team) & (df.pos_rank == pos_rank)].mean_pts.values for pos_rank in self.mean_order]
        means = team_mean_list + opp_mean_list
        return self.clean_mean_list(means)

    def add_position_rank(self, df):
        df['pos_rank'] = df.groupby(by=['team', 'position', 'week'])['mean_pts'].rank('dense', ascending=False).astype(int)
        df['pos_rank'] = df.position + df.pos_rank.astype(str)
        return df

    def add_random_pts(self, df):
        df['pts'] = ''
        for week in range(df.week.min(), df.week.max()+1):
            teams_observed = ['FA', 'FA*', 'BYE']
            for team in df[df.week == week].team.unique():
                if team not in teams_observed:
                    opp_team = df[(df.week == week) & (df.team == team)].opp.iloc[0]
                    means = self.find_game_means(df, week, team, opp_team)
                    teams_observed += [opp_team]
                    score_mat = self.gen_rand_pts(means)
                    for i, pos_rank in enumerate(self.mean_order):
                        team_player = df[(df.week == week) & (df.team == team) & (df.pos_rank == pos_rank)]
                        opp_player = df[(df.week == week) & (df.team == opp_team) & (df.pos_rank == pos_rank)]
                        if len(team_player) > 0:
                            team_idx = team_player.index[0]
                            df.at[team_idx, 'pts'] = score_mat[i, :]
                        if len(opp_player) > 0:
                            opp_idx = opp_player.index[0]
                            df.at[opp_idx, 'pts'] = score_mat[i, :]
        return df
