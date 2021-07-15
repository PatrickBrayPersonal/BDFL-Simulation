from lib import *

class Data_Generator():
    '''
    This class generates the basic data structures needed to execute the simulation
    '''
    
    def __init__(self, week):
        self.week = week
        
            
    def generate_player_proj_dict(self):
        '''
        generates the player mean score dictionary
        uses expert projections from fantasypros.com
        '''
        df_list = [None]*len(pos_list)
        for i, pos in enumerate(pos_list):
            df = pd.read_csv('../data/Season Projections/20210707/FantasyPros_Fantasy_Football_Projections_' + pos + '.csv')
            # TODO Print last modified date
            df = df[['Player', 'FPTS']]
            df = df.iloc[1:]
            df_list[i] = df
        df = pd.concat(df_list)
        df.FPTS = df.FPTS.astype(float)
        df.index = df.Player
        del df['Player']
        plr_proj_dict = df.to_dict()['FPTS']
        assert plr_proj_dict['Zach Wilson'] == 246.2
        return plr_proj_dict
        
    
    def generate_opp_pos_dict(self):
        '''
        generates the opponent-postion normalizer dictionary
        data collected from https://www.fftoday.com/stats/fantasystats.php?Season=2020&GameWeek=Season&PosID=10&Side=Allowe
        '''
        df_list = [None]*len(pos_list)
        for i, pos in enumerate(pos_list):
            df = pd.read_excel('../data/Defensive Performance/2020/sportsref_download_' + pos + '.xlsx')
            # TODO Print last modified date
            df.rename(columns={'Unnamed: 0': 'Team',
                           'Fantasy per Game': 'PPG'},
                          inplace=True)
            df = df[['Team', 'PPG']]
            df = df.iloc[1:]
            df['Pos'] = pos
            df_list[i] = df
        df = pd.concat(df_list)
        df.PPG = df.PPG.astype(float)
        df.Team = df.Team.map(team_id_dict)
        df['AVG_PPG'] = df.groupby(by=['Pos']).transform('mean')
        df['PPG'] = df.PPG / df.AVG_PPG
        pos_opp_dict = df.groupby('Pos')[['Team','PPG']]\
               .apply(lambda x: x.set_index('Team').to_dict(orient='index'))\
               .to_dict()
        assert pos_opp_dict['QB']['NYJ']['PPG'] == 1.1905969896837476,\
            'Position dict generation, Jets defense estimated to be ' + str(opp_pos_dict['QB']['NYJ']['PPG'])
        return pos_opp_dict
    
    '''
    returns number of weeks remaining in the season
    '''



