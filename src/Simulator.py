import pandas as pd
pd.options.display.float_format = '{:,.2f}'.format

class Simulator():
    '''
    Simulates a full BDFL season, evaluating and storing outcomes and results
    '''

    def __init__(self, week, api, rep, dg, n):
        self.week = week
        self.api = api
        self.rep = rep
        self.dg = dg
        self.n = n
        self.fran_id_to_name = self.gen_fran_id_to_name()
        self.matchup_df = self.simulate()
        self.team_df = self.team_performance()
        self.rank_df = self.select_playoff_teams()
        self.outcome_df = self.team_outcomes()

    def simulate(self):
        '''
        simulates an MFL season n times
        returns a dataframe of all games that occured during each season
        '''
        # Pull fantasy schedule from MFL
        sched_list = self.api.leagueSched()['schedule']['weeklySchedule']
        score_df = self.dg.score_df.copy()
        # TODO: Simulate the playoffs
        # TODO: Simulate the bench players
        weeks_rem = range(self.week, 14)
        matchup_list = [None] * self.n * len(weeks_rem) * 6
        for run in range(0, self.n):  # Every replication of the season
            for week in weeks_rem:  # Every week in the season
                for i, matchup in enumerate(sched_list[week - 1]['matchup']):
                    id0 = matchup['franchise'][0]['id']
                    id1 = matchup['franchise'][1]['id']
                    t0_players = (score_df.week == week) & (score_df.id_franchise == id0) & (score_df['start'])
                    t1_players = (score_df.week == week) & (score_df.id_franchise == id1) & (score_df['start'])
                    team0_pts = score_df.loc[t0_players, 'pts'].str[run].sum()
                    team1_pts = score_df.loc[t1_players, 'pts'].str[run].sum()
                    mu_idx = run*len(weeks_rem)*6+(week-1)*6+i
                    matchup_list[mu_idx] = [run, week, id0, team0_pts, id1, team1_pts]
        # Store results in dataframe
        matchup_df = pd.DataFrame(matchup_list, columns=['run', 'week', 'id0', 'team0_pts', 'id1', 'team1_pts'])
        matchup_df.loc[matchup_df.team0_pts > matchup_df.team1_pts, 'winner'] = matchup_df.id0
        # TODO: Allow for ties
        matchup_df.winner = matchup_df.winner.fillna(matchup_df.id1)
        return matchup_df

    def team_performance(self):
        team_df = pd.DataFrame()
        team_df['total_wins'] = self.matchup_df.rename(columns={'winner': 'team'}).groupby('team')['week'].agg('count')
        team_df['average_wins'] = team_df.total_wins / self.n
        team_df[['total_pts', 'mean_ppg', 'std_ppg', 'max_game', 'min_game']] = \
            self.matchup_df.groupby('id0')['team0_pts'].agg(['sum', 'mean', 'std', 'max', 'min']) + \
            self.matchup_df.groupby('id1')['team1_pts'].agg(['sum', 'mean', 'std', 'max', 'min'])
        return self.show_fran_name(team_df)

    def select_playoff_teams(self):
        # # Calculate Playoffs
        rosters = self.api.league(df=True)
        df = self.matchup_df.merge(rosters[['id', 'division']], left_on='winner', right_on='id', how='left')
        gb_wins = df.groupby(['run', 'id', 'division'])['winner'].agg('count').reset_index()
        # Account for pts scored tiebreaker
        scores_df = \
            df.groupby(['run', 'id0'])['team0_pts'].agg('sum') + \
            df.groupby(['run', 'id1'])['team1_pts'].agg('sum')
        rank_df = gb_wins.merge(scores_df.reset_index(), left_on=['id', 'run'], right_on=['id0', 'run'])
        # Normalize season points scores between 0 and 1
        normalized_scores = rank_df[0]/rank_df[0].max()
        rank_df['score'] = rank_df['winner'] + normalized_scores
        rank_df['div_rank'] = rank_df.groupby(['run', 'division'])['score'].rank(ascending=False)
        # Award at large bids
        rank_df['league_rank'] = rank_df.groupby(['run'])['score'].rank(ascending=False)
        rank_df['wildcard_rank'] = rank_df.loc[rank_df.div_rank > 1, :]\
            .groupby(['run'])['score']\
            .rank(ascending=False)
        rank_df['made_playoffs'] = (rank_df.wildcard_rank < 3) | (rank_df.div_rank == 1)
        del rank_df[0]
        return rank_df

    def team_outcomes(self):
        outcome_df = pd.DataFrame(self.rank_df.groupby('id')['made_playoffs'].agg('mean'))
        outcome_df['average_league_finish'] = self.rank_df.groupby('id')['league_rank'].agg('mean')
        return self.show_fran_name(outcome_df)

    def gen_fran_id_to_name(self):
        fran_list = self.api.league()['league']['franchises']['franchise']
        fran_id_to_name = {fran['id']: fran['name'] for fran in fran_list}
        return fran_id_to_name

    def show_fran_name(self, df):
        df.index = df.index.map(self.fran_id_to_name)
        return df


