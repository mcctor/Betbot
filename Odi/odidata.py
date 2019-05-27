import time
import datetime

import requests

from requests import exceptions
from bs4 import BeautifulSoup


class Odidata:

    _website_link = "https://odibets.com"
    _livegames_link = "https://odibets.com/live?sport=1"

    _candidate_live_games = list()
    _candidate_match_links = list()
    _first_basis_candidate_market_buttons_list = list()
    _second_basis_candidate_market_buttons_list = list()

    _first_basis_ready_bet_buttons_list = list()
    _second_basis_ready_bet_buttons_list = list()

    _home_info = True

    def _fetch_livegames_html(self):
        """
        This private method uses the requests module to send a GET request to https://odibets.com/live?sports=1,
        therefore obtaining information regarding all currently ongoing live games.

        :return:
                    Returns a list of Tag Objects containing the Live-Games-Page html
        """

        # Exception Handler in case of Connection Error
        try:
            # Send a GET request to the Live-Games-Page
            live_games_raw_html = requests.get(url=self._livegames_link)

            # Converts the raw html fetched above into a Soup object
            live_games_html_soup = BeautifulSoup(live_games_raw_html.content, 'html.parser')

            # A list to hold live games Tag Objects parsed from the above parent Soup Object
            live_games_tags_list = list()

            # Parse out all html tags containing live games
            for live_games in live_games_html_soup.find_all('div', attrs={'class': 'l-events-games market-3'}):
                live_games_tags_list.append(live_games)

            return live_games_tags_list

        except exceptions.ConnectionError:
            print("<[{}]> Connection Error ... Will retry fetching live games in 10 seconds.\b"
                  .format(str(datetime.datetime.now())))

            # Delay for 10 seconds before trying to fetch the resource again
            time.sleep(10.0)

            # Retry fetching the livegames html
            self._fetch_livegames_html()

    def _organize_sports_data(self, match_data):
        """
        This private method organizes the match_data into a JSON-like data structure with added information that is
        required to be known regrading a match game.

        :param match_data:
                            A Tag object representing a match's data
        :return:
                            A JSON-like data structure containing a match's data
        """

        # A list representing a match's data to be slowly built as method execution progresses
        match_buffer = list()

        # This for-loop is iterated twice. One iteration for the Home Team, the other for the Away Team
        for team_side in match_data:
            match_meta_data = team_side.parent.find_all('div', attrs={'class': 'meta'})

            # Parses out current match time and converts it to a string. It takes the format of " <time>' "
            match_time = match_meta_data[0].span.contents[-1].string

            if match_time is None:
                match_time = "HT"

            data = {
                "meta": {
                    "match_id_url": self._website_link + team_side.parent['href'],
                    "match_time": match_time,
                    }
                }

            # Ensures there is only one 'meta' key for each match as this for-loop will be iterated twice for the
            # two teams present in each match.
            try:
                match_buffer.pop(0)
                match_buffer.insert(0, data)
            except IndexError:
                match_buffer.insert(0, data)

            # Checks to see if the current entry to be recorded in this for-loop iteration is for
            # the Home Team or Away Team. Once the entry has recorded, the `_home_info` variables is
            # converted to the opposite truth value in this way, a Home-Away pattern is assured.
            if self._home_info:
                try:
                    try:
                        team_name = team_side.contents[0]

                        if team_side.span.string == 'null' or team_side.span.string is None:
                            team_goals = '0'

                        else:
                            team_goals = team_side.span.string

                        match_sides_data = {
                            "home": {"team": team_name, "goals": team_goals}
                        }
                    except AttributeError:
                        self._home_info = False
                        continue
                except IndexError:
                    self._home_info = False
                    continue

                match_buffer.append(match_sides_data)
                self._home_info = False

            else:
                try:
                    try:
                        team_name = team_side.contents[1]

                        if team_side.span.string == 'null' or team_side.span.string is None:
                            team_goals = '0'

                        else:
                            team_goals = team_side.span.string

                        match_sides_data = {
                            "away": {"team": team_name, "goals": team_goals}
                        }
                    except AttributeError:
                        self._home_info = True
                        continue
                except IndexError:
                    self._home_info = True
                    continue

                match_buffer.append(match_sides_data)
                self._home_info = True

        return match_buffer

    def _cleaned_live_games(self):
        """
        This private method finalizes on the data cleaning, returning a complete JSON-like data structure
        containing all live games.

        :return:
                    A JSON-like data structure containing all live games and associated meta_data.
        """

        # Fetch all Live-Games-Page HTML
        live_games_html = self._fetch_livegames_html()

        # A list to hold all live games as they are parsed out
        live_games_json = list()

        if live_games_html is not None:
            for match in live_games_html:
                for event in match.find_all('div', attrs={'class': 'event'}):
                    match_data = event.find_all('span', attrs={'class': 'team'})
                    single_parsed_live_game = self._organize_sports_data(match_data=match_data)

                    # append a set of home and away teams. That constitutes as a single game
                    live_games_json.append(single_parsed_live_game)

            return live_games_json

        # HTML might have contained nothing, so we try executing the method again if that was the case
        else:
            print('<[{}]> Live-Games-Page returned None ... will retry in 5 seconds'
                  .format(str(datetime.datetime.now())))
            # Wait for 5 seconds before trying again
            time.sleep(5)
            self._cleaned_live_games()

    def _select_appropriate_matches(self, live_games_json, minimum_time=50):
        """
        This private method selects matches that are ripe for betting. For now, the default criteria for a ripe bet is
        that the game is past the 50th mark.

        :param live_games_json:
                                    A JSON-like data structure with current live games
        :return:
                                    A JSON-like data structure containing bet candidates
        """

        # Ensure candidate live games list is empty on each call of this method
        self._candidate_live_games = list()

        for game in live_games_json:
            try:
                try:
                    game_time = game[0]['meta']['match_time']

                    if game_time != "HT":
                        if int(game_time.strip('\'')) > minimum_time:
                            self._candidate_live_games.append(game)

                except KeyError:
                    continue

            except ValueError:
                continue

        return self._candidate_live_games

    def _parse_candidate_match_links(self, minimum_time=50):
        """
        This method parses out the match-links for all candidate live games and organizes them into
        a list.

        :return:
                    A list of strings representing candidate live games' match-links
        """

        # Ensure candidate_match_links list is empty on each call of this method
        self._candidate_match_links = list()

        # Fetch appropriate games that meet `self._select_appropriate_matches` criteria
        candidate_games = self._select_appropriate_matches(self._cleaned_live_games(), minimum_time=minimum_time)

        for candidate in candidate_games:
            self._candidate_match_links.append(candidate[0]['meta']['match_id_url'])

        return self._candidate_match_links

    def _fetch_first_basis_candidate_match_markets(self, minimum_time=50, min_odd=1.15, max_odd=1.25):
        """
        This private method will fetch all the OVER/UNDER markets for all candidate live games and
        organize them into a market list. To do this, it will first need to parse out the match_links for
        all candidate matches.

        :param minimum_time:
                    An integer representing the minimum time game has to be in to be considered as a live bet.

        :param min_odd:
                    A float representing the minimum value some market's odd can be.

        :param max_odd:
                    A float representing the maximum value some market's odd can be.

        :return:
                    A list of candidate market buttons containing information needed to place a bet.
        """

        # Ensure first_basis_candidate_market_buttons list is empty after each call to this method
        self._first_basis_candidate_market_buttons_list = list()

        candidate_match_links = self._parse_candidate_match_links(minimum_time=minimum_time)
        max_odd_value = max_odd        # Acts like the maximum odd value that can be bet against
        min_odd_value = min_odd        # Acts like the minimum odd value that can be bet against

        for match_link in candidate_match_links:
            match_market = requests.get(url=match_link)

            match_market_soup = BeautifulSoup(match_market.content, 'html.parser')

            # Parse out over/under markets from the match_market_html_soup
            for market_types in match_market_soup.find_all('div', attrs={'class': 'market'}):

                if market_types.div.string == "Over/Under":
                    for over_under_market in market_types.find_all('div', attrs={'class': 'market-odds col-2'}):
                        for market in over_under_market.find_all('div'):
                            try:
                                # Skips the market if its button is disabled
                                if market.button['disabled']:
                                    continue

                            except KeyError:
                                market_odd_value = float(market.button['oddvalue'])
                                if market_odd_value <= max_odd_value >= min_odd_value:
                                    self._first_basis_candidate_market_buttons_list.append(market.button)

        return self._first_basis_candidate_market_buttons_list

    def _fetch_second_basis_candidate_match_markets(self, minimum_time=50, min_odd=1.8, max_odd=2.3):
        """
        This private method will fetch all the Odd/Even markets for all candidate live games and
        organize them into a market list. To do this, it will first need to parse out the match_links for
        all candidate matches.

        :param minimum_time:
                    An integer representing the minimum time game has to be in to be considered as a live bet.

        :param min_odd:
                    A float representing the minimum value some market's odd can be.

        :param max_odd:
                    A float representing the maximum value some market's odd can be.

        :return:
                    A list of candidate market buttons containing information needed to place a bet
        """

        # Ensure second_basis_candidate_market_buttons list is empty after each call to this method
        self._second_basis_candidate_market_buttons_list = list()

        candidate_match_links = self._parse_candidate_match_links(minimum_time=minimum_time)
        max_odd_value = max_odd  # Acts like the maximum odd value that can be bet against
        min_odd_value = min_odd  # Acts like the minimum odd value that can be bet against

        for match_link in candidate_match_links:
            match_market = requests.get(url=match_link)

            match_market_soup = BeautifulSoup(match_market.content, 'html.parser')

            # Parse out over/under markets from the match_market_html_soup
            for market_types in match_market_soup.find_all('div', attrs={'class': 'market'}):

                if market_types.div.string == "Odd/even":
                    for over_under_market in market_types.find_all('div', attrs={'class': 'market-odds col-2'}):
                        for market in over_under_market.find_all('div'):
                            try:
                                # Skips the market if its button is disabled
                                if market.button['disabled']:
                                    continue

                            except KeyError:
                                market_odd_value = float(market.button['oddvalue'])
                                if market_odd_value <= max_odd_value >= min_odd_value:
                                    self._second_basis_candidate_market_buttons_list.append(market.button)

        return self._second_basis_candidate_market_buttons_list

    @staticmethod
    def _parse_bet_button_metadata(bet_button_attributes):
        """
        This private method organizes information contained within a bet-button required to successfully place a bet.

        :param bet_button_attributes:
                                        A tag object containing information of a bet market.
        :return:
                    Returns bet attributes required to place a bet in form of a JSON-like Data Structure.
        """
        try:
            bet_metadata = {
                "match_id": bet_button_attributes['id'],
                "parent_match_id": bet_button_attributes['parentmatchid'],
                "home_team": bet_button_attributes['hometeam'],
                "away_team": bet_button_attributes['awayteam'],
                "start_time": bet_button_attributes['starttime'],
                "periodic_time": bet_button_attributes['periodictime'],
                "sport_id": bet_button_attributes['sportid'],
                "sub_type_id": bet_button_attributes['subtypeid'],
                "oddtype": bet_button_attributes['oddtype'],
                "live": bet_button_attributes['live'],
                "outcome_id": bet_button_attributes['outcomeid'],
                "outcome_name": bet_button_attributes["outcomename"],
                "outcome_alias": bet_button_attributes["outcomealias"],
                "odd_value": bet_button_attributes["oddvalue"],
                "specifiers": bet_button_attributes["specifiers"],
                "custom": bet_button_attributes["custom"],
                "freebet": '0'
            }
            return bet_metadata

        except KeyError:
            return None

    def first_basis_ready_bet_buttons(self, minimum_time=50, min_odd=1.15, max_odd=1.25):
        """
        This private method parses out information present in `_candidate_market_buttons` needed to
        successfully place a bet. It then organizes that data into a JSON-like data structure.

        :param minimum_time:
                    An integer representing the minimum time game has to be in to be considered as a live bet.

        :param min_odd:
                    A float representing the minimum value some market's odd can be.

        :param max_odd:
                    A float representing the maximum value some market's odd can be.

        :return:
                    A JSON-like Data Structure of ready to be placed bets
        """

        # Ensure first_basis_ready_bet_buttons list is empty on each call of this method
        self._first_basis_ready_bet_buttons_list = list()

        candidate_market_buttons = self._fetch_first_basis_candidate_match_markets(
            minimum_time=minimum_time,
            min_odd=min_odd,
            max_odd=max_odd
        )

        # Check if there are no candidate bets at this time
        if len(candidate_market_buttons) > 0:

            for button in candidate_market_buttons:
                button_attributes = self._parse_bet_button_metadata(button)

                # Ensure the game is live
                if button_attributes['live'] == "1" or button_attributes['live'] == "0":
                    self._first_basis_ready_bet_buttons_list.append(button_attributes)

            return self._first_basis_ready_bet_buttons_list

        else:
            # print("<[{}]> No candidate bets at this time.".format(str(datetime.datetime.now())))
            return self._first_basis_ready_bet_buttons_list

    def second_basis_ready_bet_buttons(self, minimum_time=50, min_odd=1.8, max_odd=2.2):
        """
        This private method parses out information present in `self._candidate_market_buttons` needed to
        successfully place a bet. It then organizes that data into a JSON-like data structure.

        :param minimum_time:
                    An integer representing the minimum time game has to be in to be considered as a live bet.

        :param min_odd:
                    A float representing the minimum value some market's odd can be.

        :param max_odd:
                    A float representing the maximum value some market's odd can be.

        :return:
                   A JSON-like Data Structure of ready to be placed bets
        """

        # Ensure second_basis_ready_bet_buttons list is empty on each call of this method
        self._second_basis_ready_bet_buttons_list = list()

        candidate_market_buttons = self._fetch_second_basis_candidate_match_markets(
            minimum_time=minimum_time,
            min_odd=min_odd,
            max_odd=max_odd
        )

        # Check if there are no candidate bets at this time
        if len(candidate_market_buttons) > 0:

            for button in candidate_market_buttons:
                button_attributes = self._parse_bet_button_metadata(button)

                if button_attributes is not None:

                    # Ensure the game is not live
                    if button_attributes['live'] == "0":
                        self._second_basis_ready_bet_buttons_list.append(button_attributes)

            return self._second_basis_ready_bet_buttons_list

        else:
            # print("<[{}]> No candidate bets at this time.".format(str(datetime.datetime.now())))
            return self._second_basis_ready_bet_buttons_list
