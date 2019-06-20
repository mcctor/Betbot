import time
import math
import datetime
import logging
import random
import json

import requests

from requests import exceptions
from bs4 import BeautifulSoup

from Odi.odidata import Odidata
from Database.database_model import db_session, BetHistory


class Odibets(Odidata):

    _base_website_link = "https://odibets.com"
    _login_link = "https://odibets.com/login"
    _account_link = "https://odibets.com/account"
    _my_bets_link = "https://odibets.com/my-bets"
    _withdraw_link = "https://odibets.com/withdraw"

    _addbet_link = "https://odibets.com/bet/add"
    _closed_bet_link = "https://odibets.com/my-bets?tab=2"
    _bet_link = "https://odibets.com/bet"
    _set_bet_stake_link = "https://odibets.com/bet/stake"

    _session = requests.Session()
    _account_balance = float()

    _open_bet_links = list()
    _open_bets_info = list()

    def __init__(self, phone_number, account_password):
        # Initialize super class
        self.odidata = super()

        # Initialize class by logging in user
        self._login_user(phone_number, account_password)

    def _login_user(self, phone_number, account_password):
        login_data = {
            "msisdn": str(phone_number),
            "password": str(account_password)
        }

        try:
            self._session.post(url=self._login_link, data=login_data)

            logging.info('Successfully logged in User: %s', phone_number)
            return self._session

        except exceptions.ConnectionError:
            logging.warn('Connection error preventing Logging-In of user.')

            # Wait for 3 seconds before trying to log in again.
            time.sleep(3.0)
            self._login_user(phone_number, account_password)

    @property
    def account_balance(self):
        """
        This method queries the account web-page to get the user's current account balance.

        :return:
                    A float object declaring the account's balance.
        """

        # Use the authenticated `requests.Session` object
        authenticated_session = self._session

        # Handle exception in case of Connection Error
        try:
            # Fetch account-page
            account_html = authenticated_session.get(url=self._account_link)

            # Convert fetched html to a Soup Object
            account_html_soup = BeautifulSoup(account_html.content, 'html.parser')

            # Parse out account balance from html soup
            for amount in account_html_soup.find_all('div', attrs={'class': 'l-mac-amount-withdrawable'}):
                money_str = amount.h3.string.strip('Ksh. ')
                money = float(money_str.replace(',', ''))

                self._account_balance = money
                logging.info('Account balance fetched. Currently at %s', self._account_balance)

                return self._account_balance

        except exceptions.ConnectionError:
            raise Exception("Cannot fetch account balance. Check your internet connection.")

    def _my_open_bets_links(self):
        """
        This method fetches all open currently-ongoing bets from the user's account. It then parses out their bet-links
        and organizes them into a list containing all current open bets.

        :return:
                    A list containing all open currently-ongoing bets.
        """

        # Ensure open_bets_links list is empty at each call of this method
        self._open_bet_links = list()

        # Use the authenticated `requests.Session` object
        authenticated_session = self._session

        # Handle exception in case of Connection Error
        try:
            # Fetch open-bets page
            open_bets_html = authenticated_session.get(url=self._my_bets_link)

            # Convert fetched html to a Soup Object
            open_bets_html_soup = BeautifulSoup(open_bets_html.content, 'html.parser')

            # Parse out my_bets from html soup
            for my_bets_section in open_bets_html_soup.find_all('div', attrs={'class': 'l-mybets-section'}):
                for open_bet in my_bets_section.find_all('a'):
                    self._open_bet_links.append(self._base_website_link + '/' + open_bet['href'])

            logging.info('Open bets have been fetched.')
            return self._open_bet_links

        except exceptions.ConnectionError:
            raise Exception("Cannot fetch account's open bets. Check your internet connection.")

    @staticmethod
    def _normalize_my_bets_info(match_title):
        """
        This method is used to strip out white space and unneeded information

        :param match_title:
        :return:
        """

        match_teams_list = list()

        # remove the date and time part of the string
        teams_and_whitespace = match_title[:-25]

        # strip unneeded whitespace from the string
        stripped_teams = teams_and_whitespace.lstrip().rstrip()

        # Split the Home and Away team and put them into a list
        home_away_list = stripped_teams.split('—')

        for team in home_away_list:
            if len(team.split()) > 2 or team.split()[-1].isnumeric:
                norm_team = team.split()[0] + " " + team.split()[1]
                match_teams_list.append(norm_team.lstrip().rstrip())

            else:
                match_teams_list.append(team.lstrip().rstrip())

        return list(match_teams_list)

    def _my_bets_info(self):
        """
        This method is meant to capture which teams have current ongoing bets. This is so that a match which is
        already staked shouldn't be staked twice.

        :return:
                    A list containing the names of the playing teams that have already been staked.
        """
        # A list to hold lists representing the home and away team of each open bet
        open_bets_info = list()

        # Use the authenticated `requests.Session` object
        authenticated_session = self._session

        # Fetch the list of open-bets links
        open_bets_links = self._my_open_bets_links()

        for bet_link in open_bets_links:
            # Fetch bet link HTML
            bet_link_html = authenticated_session.get(url=bet_link)

            # Change the fetched HTML into a Soup Object
            bet_link_html_soup = BeautifulSoup(bet_link_html.content, 'html.parser')

            # Parse match_titles from html soup
            for match_title in bet_link_html_soup('div', attrs={'class': 'match-title'}):
                open_bets_info.append(self._normalize_my_bets_info(match_title.text))

        self._open_bets_info = open_bets_info
        return self._open_bets_info

    def withdraw_money(self, amount):
        """
        This method is used to withdraw money from the user's account. The minimum amount that can be
        withdrawn is Ksh. 100.

        :param amount:
                        An integer object not less than 100
        :return:
                        An integer object representing the balance left in the account
        """

        # Ensure withdraw-amount is equal or greater than Ksh. 100
        if amount < 100:
            raise Exception("Withdraw amount is below the minimum allowable amount.")

        # Use the authenticated `requests.Session` object
        authenticated_session = self._session

        # Data needed to feel the withdraw-page form
        withdraw_data = {
            "amount": str(amount)
        }

        try:
            authenticated_session.post(url=self._withdraw_link, data=withdraw_data)
            logging.info('Amount %s has been withdrawn from account', self.account_balance)
            return self.account_balance

        except exceptions.ConnectionError:
            raise Exception("Failed to withdraw specified amount. Check your internet connection.")

    def _previous_closed_bet_metadata(self):
        # Use the authenticated `requests.Session` object
        authenticated_session = self._session

        try:
            # Get closed bets html
            request = authenticated_session.get(url=self._closed_bet_link)

            html_soup = BeautifulSoup(request.content, 'html.parser')

            latest_closed_bet = html_soup.find('div', attrs={'class': 'l-mybets-section-body'}).a

            latest_closed_bet_json = {
                "bet_href_id": latest_closed_bet['href'],
                "won": self._check_if_closed_bet_won(latest_closed_bet),
                "bet_odds": self._get_closed_bet_total_odd(latest_closed_bet),
                "net_profit": math.ceil(self._calculate_closed_bet_profit(latest_closed_bet))
            }

            return latest_closed_bet_json

        except requests.ConnectionError:
            raise Exception("Failed to fetch closed bets html.")

    def _update_db(self):
        # Fetch the data to be inserted into the database
        update_data = self._previous_closed_bet_metadata()

        # Create a new row/entry for the database
        latest_closed_bet_data = BetHistory(
            bet_href=update_data['bet_href_id'],
            won=update_data['won'],
            bet_odds=update_data['bet_odds'],
            profit=update_data['net_profit']
        )

        # Add the new row to the database and commit
        db_session.add(latest_closed_bet_data)
        db_session.commit()

    @staticmethod
    def _check_if_closed_bet_won(closed_bet_tag_object):
        # check to see if latest bet was won
        if closed_bet_tag_object.find('div', attrs={'class': 'bet-towin'}).small.string == 'Won':
            return 1
        else:
            return 0

    @staticmethod
    def _get_closed_bet_total_odd(closed_bet_tag_object):
        # Parse out odd section from the closed_bet_tag_object
        odd_section = closed_bet_tag_object.find_all('div', attrs={'class': 'bet-details-s'})[1]

        # Type cast string to float, and return the result
        return float(odd_section.find('span', attrs={'class': 'd'}).string)

    @staticmethod
    def _calculate_closed_bet_profit(closed_bet_tag_object):
        # Parse out stake section from the closed_bet_tag_object
        stake_section = closed_bet_tag_object.find_all('div', attrs={'class': 'bet-details-s'})[-1]

        # Typecast stake to float
        stake = float(stake_section.find('span', attrs={'class': 'd'}).string.strip('KES. '))

        # Typecast total winnings to float
        total_profit = float(
            closed_bet_tag_object.find('div', attrs={'class': 'bet-towin'}).div.string.strip('KES. '))

        # Calculate the closed bet net profit
        net_profit = total_profit - stake

        return net_profit

    def _add_bet_to_betslip(self, match_id, parent_match_id, home_team, away_team, start_time, periodic_time, sport_id,
                            sub_type_id, oddtype, live, outcome_id, outcome_name, outcome_alias, odd_value, specifiers,
                            custom, freebet):

        # Use the authenticated `requests.Session` object
        authenticated_session = self._session

        # A bunch of verbose nonsense needed to place a bet
        params = "match_id=" + match_id + "&sub_type_id=" + sub_type_id + "&outcome_name=" + \
                 outcome_name.replace("+", "%2B").replace("&", "%26") + "&outcome_alias=" + \
                 outcome_alias.replace("+", "%2B").replace("&", "%26") + "&specifiers=" + \
                 specifiers.replace("+", "%2B") + "&live=" + live + "&home_team=" + home_team + \
                 "&away_team=" + away_team + "&outcome_id=" + outcome_id.replace("+", "%2B") + \
                 "&odd_value=" + odd_value + "&odd_type=" + oddtype + "&parent_match_id=" + \
                 parent_match_id + "&sport_id=" + sport_id + "&start_time=" + start_time + \
                 "&periodic_time=" + periodic_time + "&custom=" + custom + '&freebet=' + freebet

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Charset": "utf-8"
        }
        try:
            add_bet_action = authenticated_session.post(url=self._addbet_link, data=params, headers=headers)
            logging.info('Game successfully added to betslip.')
            return add_bet_action

        except exceptions.ConnectionError:
            raise Exception('Failed to add bets to betslip. Check your internet connection.')

    def add_first_basis_games_to_betslip(self, minimum_time=50, min_odd=1.15, max_odd=1.25):
        """
        The major purpose of this method is to ensure that no game has more than one bet associated to it.
        Once this condition is ensured, each of the games are added to a bet slip. Another limit that is
        ensured is the number of bets for each betslip. For now, I will limit it to a maximum of five.

        :return:
        """

        # Fetch candidate bets' buttons to be involved in a bet
        candidate_games = self.odidata.first_basis_ready_bet_buttons(
            minimum_time=minimum_time,
            min_odd=min_odd,
            max_odd=max_odd
        )

        # Fetch all the home-away teams which already are involved in a bet
        open_bets_info = self._my_bets_info()

        # A list to hold each open-bets' home team
        open_bet_home_teams = list()

        # Append all the home teams to the open_bet_home_teams list
        for match in open_bets_info:
            open_bet_home_teams.append(match[0])

        # Check if there are any candidate games ready to be added to betslip
        if len(candidate_games) == 0:
            logging.info('No candidate bet at this time. Waiting for 2 minutes before trying again.')
            time.sleep(120)
            return False

        # Select one of the candidate games button randomly
        button = candidate_games[random.randint(0, len(candidate_games)-1)]

        try:
            button_team = button['home_team'].split()[0] + " " + button['home_team'].split()[1]

        except IndexError:
            button_team = button['home_team'].split()[0]

        # Ensure the team is not already involved in a bet
        if button_team not in open_bet_home_teams:
            betslip = self._add_bet_to_betslip(
                match_id=button['match_id'],
                parent_match_id=button['parent_match_id'],
                home_team=button['home_team'],
                away_team=button['away_team'],
                start_time=button['start_time'],
                periodic_time=button['periodic_time'],
                sport_id=button['sport_id'],
                sub_type_id=button['sub_type_id'],
                oddtype=button['oddtype'],
                live=button['live'],
                outcome_id=button['outcome_id'],
                outcome_name=button['outcome_name'],
                outcome_alias=button['outcome_alias'],
                odd_value=button['odd_value'],
                specifiers=button['specifiers'],
                custom=button['custom'],
                freebet=button['freebet']
            )

            # Check if the betslip was added successfully
            betslip = json.loads(betslip.content.decode('utf-8'), encoding='utf-8')
            if betslip['status_code'] == 200:
                logging.info('Successfully added First Basis Bet: %s to betslip', button['match_id'])

                # Update database with the result of the previous closed bet
                self._update_db()

                return True

        else:
            print("<[{}]> Team: \"{}\" already involved in another bet.".format(
                str(datetime.datetime.now()), button['home_team']))
            return False

    def add_second_basis_games_to_betslip(self, minimum_time=50, min_odd=1.8, max_odd=2.2):
        """
        The major purpose of this method is to ensure that no game has more than one bet associated to it.
        Once this condition is ensured, each of the games are added to a bet slip. Another limit that is
        ensured is the number of bets for each betslip. For now, I will limit it to a maximum of five.

        :return:
        """

        # Fetch candidate bets' buttons to be involved in a bet
        candidate_games = self.odidata.second_basis_ready_bet_buttons(
            minimum_time=minimum_time,
            min_odd=min_odd,
            max_odd=max_odd
        )

        # Fetch all the home teams which already are involved in a bet
        open_bets_info = self._my_bets_info()

        # A list to hold each open-bets' home team
        open_bet_home_teams = list()

        # Append all the home teams to the open_bet_home_teams list
        for match in open_bets_info:
            open_bet_home_teams.append(match[0])

        # Check if there are any candidate games ready to be added to betslip
        if len(candidate_games) == 0:
            logging.info('No candidate bet at this time. Waiting for 2 minutes before trying again.')

            time.sleep(120)
            return False

        # Select one of the candidate games button randomly
        button = candidate_games[random.randint(0, len(candidate_games)-1)]

        try:
            button_team = button['home_team'].split()[0] + " " + button['home_team'].split()[1]

        except IndexError:
            button_team = button['home_team'].split()[0]

        # Ensure the team is not already involved in a bet
        if button_team not in open_bet_home_teams:
            betslip = self._add_bet_to_betslip(
                match_id=button['match_id'],
                parent_match_id=button['parent_match_id'],
                home_team=button['home_team'],
                away_team=button['away_team'],
                start_time=button['start_time'],
                periodic_time=button['periodic_time'],
                sport_id=button['sport_id'],
                sub_type_id=button['sub_type_id'],
                oddtype=button['oddtype'],
                live=button['live'],
                outcome_id=button['outcome_id'],
                outcome_name=button['outcome_name'],
                outcome_alias=button['outcome_alias'],
                odd_value=button['odd_value'],
                specifiers=button['specifiers'],
                custom=button['custom'],
                freebet=button['freebet']
            )

            # Check if the betslip was added successfully
            betslip = json.loads(betslip.content.decode('utf-8'), encoding='utf-8')
            if betslip['status_code'] == 200:
                logging.info('Successfully added First Basis Bet: %s to betslip', button['match_id'])

                # Update database with the result of the previous closed bet
                self._update_db()

                return True

        else:
            print("<[{}]> Team: \"{}\" already involved in another bet.".format(
                str(datetime.datetime.now()), button['home_team']))
            return False

    def set_bet_stake(self, amount):
        """
        This method sets the bet-stake for a specific betslip. The minimum amount is Ksh. 5

        :return:
                    Returns a 200 status code if the request was successful
        """

        # Fetch authenticated `requests.Session` Object
        authenticated_session = self._session

        stake = "stake=" + str(amount)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            stake_request = authenticated_session.post(url=self._set_bet_stake_link, data=stake, headers=headers)

            logging.info('Bet stake of %s has been set for current betslip.', amount)
            return stake_request.status_code

        except exceptions.ConnectionError:
            raise Exception("Could not set bet stake. Check your internet connection.")

    def place_all_bets(self):
        """
        This method confirms all the bets in the current session's betslip. It is wise to first set
        a stake before calling this method, otherwise the stake amount will default to Ksh. 49.

        :return:
        """

        # Fetch authenticated `requests.Session` Object
        authenticated_session = self._session

        try:
            placed_bets = authenticated_session.post(url=self._bet_link)
            logging.info('Current betslip has been placed!')
            return placed_bets

        except exceptions.ConnectionError:
            raise Exception("Failed to confirm and place Betslip. Check your internet connection.")
