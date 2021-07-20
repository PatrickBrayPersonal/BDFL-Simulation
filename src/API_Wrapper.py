"""
Python wrapper the www.myfantasyleague.com API
"""

import logging
import pprint
from datetime import date
import pandas as pd
import requests
import requests_cache
# this function call will transparent cache new API requests, and use the cahce whenever we make a repeated call
requests_cache.install_cache()

__all__ = ['API']

# initialize a logger so any loggers in the caller
# can see what's going on
_logger = logging.getLogger(__name__)


class API(object):
    """
    Class providing wrappers to the MFL API calls
    The leagueid parameter is the MFL league ID. The year parameter
    defaults to the current year. The json parameter controls the result format.
    If set to True (the default), JSON data is returned. Otherwise XML is returned.
    The fail_on_error parameter will cause requests.exceptions.HTTPError to be thrown
    on a failed request. Full MFL API docs are at http://www03.myfantasyleague.com/2016/export
    NOTE: At this time this API does not support any call requiring authentication to MFL
    """

    def __init__(self, leagueid=None, year=date.today().year, user_agent=None, json=True, fail_on_error=True):
        self.leagueid = leagueid
        self.url = 'https://api.myfantasyleague.com/{}/export?'.format(year)
        self.json = json
        self._first_req = True
        self._fail_on_error = fail_on_error
        self.user_agent = user_agent

    def _call_mfl(self, params):
        if self.json:
            params['JSON'] = 1
        else:
            params['JSON'] = 0

        if self.user_agent:
            headers = {
                'User-Agent': self.user_agent
            }
        else:
            headers = {}

        _logger.debug('Making request to %s', self.url)
        _logger.debug('Params: %s', pprint.pformat(params))
        results = requests.get(self.url, headers=headers, params=params)
        if self._fail_on_error:
            # will throw an exception if the status code indicates failure
            results.raise_for_status()

        if self._first_req:
            # MFL redirects the first time you hit it's API. We want to save the URL
            # so future requests don't have the overhead of being redirected
            _logger.debug('First time requesting to MFL. Setting URL after redirects')
            param_remover = slice(results.url.find('?'))
            self.url = results.url[param_remover]
            self._first_req = False

        if self.json:
            return results.json()
        else:
            return results.text

    def _check_leagueid(self):
        try:
            self.leagueid = int(self.leagueid)
        except ValueError:
            _logger.error('leagueid is %s', self.leagueid)
            raise ValueError('leagueid must be an integer for this call')

    def players(self, players=None, df=False, since=None, details=None):
        """
        Pull the MFL player DB. The players parameter, if specified,
        should be a comma-seperated string of MFL player IDs. The since parameter,
        if specified, should be an epoch timestamp specifying the oldest date you want
        the information for. The details parameter, if specified, gets extra information
        about each player
        """
        # requests won't send any parameter whose value is None
        params = dict(TYPE='players', L=self.leagueid, PLAYERS=players, SINCE=since)
        if details:
            params['DETAILS'] = 1
        response = self._call_mfl(params)
        if df:
            response = response['players']['player']
            if type(response) != list:
                response = [response]
            response = pd.DataFrame.from_dict(response)
        return response

    def allRules(self):
        """
        All scoring rules that MyFantasyLeague.com currently supports.
        Data returned here is needed to understand results of MFL.rules()
        """
        return self._call_mfl(dict(TYPE='allRules'))

    def injuries(self):
        """
        The player ID, status (IR, Out, Questionable, Doubtful, Probable) and details
        i.e., 'Knee', 'Foot', 'Ribs', etc.) of all players on the official NFL injury report.
        """
        return self._call_mfl(dict(TYPE='injuries'))

    def nflSchedule(self, weeknum='', year=date.today().year, df=False):
        """
        The NFL schedule for one week of the season. The weeknum parameter defaults to the current week
        If specified, weeknum should be a number between representing the week of the NFL schedule
        """
        if weeknum != '':
            weeknum = '_'+str(weeknum)
        url = 'https://api.myfantasyleague.com/fflnetdynamic{}/nfl_sched{}.json'.format(year, weeknum)

        results = requests.get(url).json()
        if df==True:
            print('TODO')
        return results
        

    def adp(self, **kwargs):
        """
        Get ADP data from MFL. Any keyword args will be passed to MFL in the request.
        This parameter has many optional flags. For a full description see the MFL documentation
        """
        kwargs['TYPE'] = 'adp'
        response = self._call_mfl(kwargs)
        return response

    def aav(self, **kwargs):
        """
        Get AAV data from MFL. Any keyword args will be passed to MFL in the request.
        This parameter has many optional flags. For a full description see the MFL documentation
        """
        kwargs['TYPE'] = 'aav'
        return self._call_mfl(kwargs)

    def topAdds(self):
        """The most-added players across all MyFantasyLeague.com-hosted leagues"""
        return self._call_mfl(dict(TYPE='topAdds'))

    def topDrops(self):
        """The most-dropped players across all MyFantasyLeague.com-hosted leagues"""
        return self._call_mfl(dict(TYPE='topDrops'))

    def topStarters(self):
        """The most-started players across all MyFantasyLeague.com-hosted leagues"""
        return self._call_mfl(dict(TYPE='topStarters'))

    def topOwns(self):
        """The most-owned players across all MyFantasyLeague.com-hosted leagues"""
        return self._call_mfl(dict(TYPE='topOwns'))

    def league(self, df=False):
        """
        General league setup parameters for a given league.
        NOTE: Authentication is currently not supported so no commisher-specific
        information will be returned
        """
        self._check_leagueid()
        params = dict(TYPE='league', L=self.leagueid)
        response = self._call_mfl(params)
        if df:
            response = pd.DataFrame.from_dict(response['league']['franchises']['franchise'])
        return response

    def rules(self):
        """League scoring rules for a given league. allRules() should be called to interpret the abbreviations"""
        self._check_leagueid()
        params = dict(TYPE='rules', L=self.leagueid)
        return self._call_mfl(params)

    def rosters(self, franchiseid=None, df=False):
        """
        The current rosters for all franchises in a league.
        The franchiseid parameter, if specified, limits the results to one franchise
        """
        self._check_leagueid()
        params = dict(TYPE='rosters', L=self.leagueid, FRANCHISE=franchiseid)
        response = self._call_mfl(params)
        if df:
            response = pd.DataFrame.from_dict(response['rosters']['franchise'])
            response = self.explode_list_dict_col(response, 'player', 'id')
        return response

    def leagueStandings(self):
        """The current league standings for a given league"""
        self._check_leagueid()
        params = dict(TYPE='leagueStandings', L=self.leagueid)
        return self._call_mfl(params)

    def weeklyResults(self, weekspec=None):
        """The weekly results for a given league/week. weekspec can be 'YTD' to get all results"""
        self._check_leagueid()
        params = dict(TYPE='weeklyResults', L=self.leagueid, W=weekspec)
        return self._call_mfl(params)

    def liveScoring(self, df=False, details=False, **kwargs):
        """
        Live scoring for a given league and week.
        The details parameter provides more information on the scores
        """
        self._check_leagueid()
        params = dict(TYPE='liveScoring', L=self.leagueid)
        params.update(kwargs)
        if details:
            params['DETAILS'] = 1
        response = self._call_mfl(params)
        if df:
            response = response['liveScoring']['matchup']
        return response

    def playerScores(self, weeknum=None, df=False, **kwargs):
        """
        All player scores for a given league/week. This has a lot of options so any keyword args,
        other than weeknum, passed will be passed through to MFL. See the MFL API documentation for
        supported options
        """
        self._check_leagueid()
        params = dict(TYPE='playerScores', W=weeknum, L=self.leagueid)
        params.update(kwargs)
        response = self._call_mfl(params)
        if df:
            response = pd.DataFrame.from_dict(response['playerScores']['playerScore'])
        return response

    def draftResults(self):
        """Draft results for a given league"""
        self._check_leagueid()
        params = dict(TYPE='draftResults', L=self.leagueid)
        return self._call_mfl(params)

    def futureDraftPicks(self):
        """Future Draft Picks for a given league"""
        self._check_leagueid()
        params = dict(TYPE='futureDraftPicks', L=self.leagueid)
        return self._call_mfl(params)

    def auctionResults(self):
        """Auction results for a given league"""
        self._check_leagueid()
        params = dict(TYPE='auctionResults', L=self.leagueid)
        return self._call_mfl(params)

    def freeAgents(self, position=None):
        """
        Fantasy free agents for the league. If position is specified
        only results for that position will be shown
        """
        self._check_leagueid()
        params = dict(TYPE='freeAgents', L=self.leagueid, POSITION=position)
        return self._call_mfl(params)

    def transactions(self, trans_type=None, count=None, franchise=None, days=None):
        """
        Transactions for the league. The optional arguments allow for limiting the results
        The trans_type parameter limits the results to certain transaction types
        The count parameter sets a limit on the number of transactions to return
        The franchise parameter limits the results to a given franchise
        The days parameter pulls transaction for the given amount of days only
        """
        self._check_leagueid()
        params = dict(
            TYPE='transactions',
            L=self.leagueid,
            TRANS_TYPE=trans_type,
            COUNT=count,
            FRANCHISE=franchise,
            DAYS=days,
        )
        return self._call_mfl(params)

    def rss(self):
        """
        An RSS feed of key league data for the league,
        including: league standings, current week's live scoring,
        last week's fantasy results, and the five newest message board topics
        """
        self._check_leagueid()
        params = dict(TYPE='rss', L=self.leagueid)
        return self._call_mfl(params)

    def siteNews(self):
        """
        An RSS feed of MyFantasyLeague.com site news
        """
        return self._call_mfl(dict(TYPE='siteNews'))

    def projectedScores(self, playerid, weeknum=None, count=None, position=None):
        """Projected scores for a given playerid in the league's scoring system"""
        self._check_leagueid()
        params = dict(
            TYPE='projectedScores',
            L=self.leagueid,
            PLAYERS=playerid,
            W=weeknum,
            COUNT=count,
            POSITION=position,
        )
        return self._call_mfl(params)

    def leagueSearch(self, query):
        """
        Given a case-insensitive string, search for leagues containing the given string.
        query can also be an email address, allowing you to get all leagues for a given user
        """
        return self._call_mfl(dict(TYPE='leagueSearch', SEARCH=query))

    def add_col_prefix(self, df, prefix):
        '''
        adds prefix "prefix" to all columns of dataframe "df"
        '''
        # create rename dict
        rename_dict = {}
        for i in list(df.columns):
            rename_dict[i] = prefix + '_' + i
        # rename cols
        df = df.rename(columns = rename_dict)
        return df

    def explode_list_dict_col(self, df, col, keyid):
        '''
        Explodes a dataframe "df" that has a column "col" containing a list of dictionaries
        unique id for df must be provided "keyid" as string or list of strings
        '''
        df_list = [None]*len(df)
        for i in range(0,len(df)):
            entry_df = pd.DataFrame(df[col][i])
            entry_df = self.add_col_prefix(entry_df, col)
            entry_df[keyid] = df[keyid][i]
            df_list[i] = entry_df
        col_df = pd.concat(df_list)
        merged_df = pd.merge(df, col_df, on = keyid, how = 'left')
        merged_df = merged_df.drop(col, axis = 1)
        return merged_df
