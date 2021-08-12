import pandas as pd
import numpy as np
import re
from itertools import product
from math import sqrt
from src.AnalysisFunctions import AnalysisFunctions

class Data_Generator():
    '''
    This class generates the basic data structures needed to execute the simulation
    '''

    def __init__(self, week, api, rep , n=10):
        np.random.seed(0)
        self.week = week
        self.api = api
        self.rep = rep
        self.af = AnalysisFunctions('')
        self.pos_list = ['QB', 'RB', 'WR', 'TE']
        self.team_id_dict = team_id_dict = {'Arizona Cardinals': 'ARI',
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
        self.week_proj_dict = self.read_weekly_projections()
        self.plr_proj_dict = self.create_plr_proj_dict()
        self.sched_dict = self.create_sched_dict()
        self.pos_opp_dict = self.create_pos_opp_dict()
        self.n = n
        self.mean_order = ['QB1', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE1']
        self.vars_by_pos = [11, 8, 7, 10, 8.5, 8, 7]
        self.vars_df = pd.DataFrame(self.vars_by_pos).T
        self.vars_df.columns = self.mean_order # TODO: make less ugly
        self.corr_df = pd.read_excel('data/Position_correlations.xlsx', sheet_name='RAW', index_col=0)
        self.corr_mat = self.corr_df.to_numpy()
        self.cov_mat = self.create_cov_mat()
        self.score_df = self.create_score_df()
        

    def create_plr_proj_dict(self):
        '''
        generates the player mean score dictionary
        uses expert projections from fantasypros.com
        '''
        df_list = [None]*len(self.pos_list)
        for i, pos in enumerate(self.pos_list):
            df = pd.read_csv('data/Season Projections/20210707/FantasyPros_Fantasy_Football_Projections_' + pos + '.csv')
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
            df = pd.read_excel('data/Defensive Performance/2020/sportsref_download_' + pos + '.xlsx')
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

        assert round(pos_opp_dict['QB']['NYJ']['PPG'], 3) == 1.191,\
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
        # Overwrite mean points for current week
        roster_df.loc[roster_df.week == self.week, 'mean_pts'] = roster_df.norm_name_player.map(self.week_proj_dict).fillna(0)
        roster_df = self.add_position_rank(roster_df)
        # Choose BDFL starters
        roster_df = self.pick_starters(roster_df)
        # Simulate NFL games
        roster_df = self.add_random_pts(roster_df)
        return roster_df

    def gen_rand_pts(self, means):
        '''
        takes in an array of means scores for each player and outputs a 2d array of n simulations of the game
        '''
        # TODO: Anything that comes in as a 0 should leave as a 0
        # TODO: SIZE DOESN'T DO WHAT YOU THINK IT DOES
        data = np.random.multivariate_normal(means, self.cov_mat, size=self.n)
        return data

    def normalize_name(self, name):
        '''
        Accepts a name string, removes all non alphabetic characters and sets to lower
        '''
        name = ''.join(name.lower().split()[0:2])
        regex = re.compile('[^a-z]')
        name = regex.sub('', name)
        return name

    def clean_mean_list(self, ls):
        '''
        encapsulates each item of list in a list
        '''
        return [item[0] if len(item) > 0 else 0 for item in ls]

    def find_game_means(self, df, week, team, opp_team):
        '''
        returns the mean performance of each player in the relevant position ranks
        returns in the correct order for the position matrix 'mean_order'
        '''
        team_mean_list = [df[(df.week == week) & (df.team == team) & (df.pos_rank == pos_rank)].mean_pts.values *0.7 for pos_rank in self.mean_order]
        opp_mean_list = [df[(df.week == week) & (df.team == opp_team) & (df.pos_rank == pos_rank)].mean_pts.values *0.7 for pos_rank in self.mean_order]
        means = team_mean_list + opp_mean_list
        return self.clean_mean_list(means)

    def add_position_rank(self, df):
        '''
        determines how the player rates against other players of their same position on their
        NFL roster. Used in the correlations matrix
        '''
        df['pos_rank'] = df.groupby(by=['team', 'position', 'week'])['mean_pts'].rank('dense', ascending=False).astype(int)
        df['pos_rank'] = df.position + df.pos_rank.astype(str)
        return df

    def add_random_pts(self, df):
        '''
        facilitates the execution of the simulation of n NFL games for players on BDFL rosters
        correlations between player performances and mean expectations are taken into account
        '''
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
                            df.at[team_idx, 'pts'] = score_mat[:, i]
                        if len(opp_player) > 0:
                            opp_idx = opp_player.index[0]
                            df.at[opp_idx, 'pts'] = score_mat[:, i]
        return df

    def pick_starters(self, df):
        '''
        Finds the top QB and TE, Top 2 WR and RB, then the top two of the remaining RB, TE, and WR
        for each team in each week and assigns them a True in the start field
        '''
        df['fran_pos_rank'] = df.groupby(['id_franchise', 'week', 'position']).rank('dense', ascending=False).astype(int)['mean_pts']
        # Assign position starters
        df['start'] = (df.fran_pos_rank == 1) | (df.fran_pos_rank == 2) & (df.position.isin(['RB', 'WR']))
        # Assign flex starters
        flex_eligible = (~df.start) & (df.position.isin(['RB', 'WR', 'TE']))
        df.loc[flex_eligible, 'flex_rank'] = df[flex_eligible].groupby(['id_franchise', 'week']).rank('dense', ascending=False).astype(int)['mean_pts']
        df.loc[df.flex_rank < 3, 'start'] = True
        return df

    def create_cov_mat(self):
        '''
        creates the covariance matrix by multiplying
        correlation * sqrt(variance(positionA)*variance(positionB))
        '''
        vars_by_pos = self.vars_by_pos * 2
        npos = len(vars_by_pos)
        var_ls = [sqrt(a * b) for a, b in product(vars_by_pos, vars_by_pos)]
        var_mat = [None]*npos
        for i in range(0, npos):
            var_mat[i] = var_ls[i*npos: i*npos+npos]
        var_mat = np.array(var_mat)
        return var_mat @ self.corr_mat
    
    def read_weekly_projections(self):
        '''
        reads the weeks relevant folder in the weekly projections folder
        returns a datafrom of player projections
        '''
        try:
            proj_list = self.af.files_in_directory(data_folder='data/Weekly Projections/2021/week ' + str(self.week))
        except:
            print('*** NEED TO ADD NEW WEEKLY PROJECTIONS ***')
            raise ValueError
        df_list = [None] * len(proj_list)
        for i, proj in enumerate(proj_list):
            df = pd.read_csv(proj)
            df = df[['Player', 'FPTS']]
            df = df.iloc[1:]
            df_list[i] = df
        proj_df = pd.concat(df_list).dropna()
        norm_name_player = proj_df.Player.apply(self.normalize_name)
        proj_df.index = norm_name_player
        del proj_df['Player']
        proj_dict = proj_df.to_dict()['FPTS']
        return proj_dict
