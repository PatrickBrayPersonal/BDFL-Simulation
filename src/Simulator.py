import pandas as pd


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
        self.matchup_df = self.simulate()
        self.team_df = self.team_performance()

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
        return team_df
