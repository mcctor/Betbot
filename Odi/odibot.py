import time
import logging

from Odi.odibets import Odibets


class Odibot(Odibets):

    current_stake = int()

    def __init__(self, phone_number, password, stake_figure):
        super().__init__(phone_number=phone_number, account_password=password)

        # Initialize the total maximum account balance that is to be assumed
        self.current_stake = stake_figure

        # Fetch account balance that is there before any betting begins
        self.account_balance_before_staking = self.account_balance

    @property
    def is_balance_enough(self):
        # Fetch user's current account balance
        current_balance = self.account_balance

        if current_balance >= self.current_stake:
            return True
        else:
            return False

    def _ten_percent_stake(self):

        if self.is_balance_enough:
            stake = (10/100) * self.current_stake
            self.set_bet_stake(amount=int(stake))

            self.current_stake = self.current_stake - stake

            return self.current_stake

        else:
            raise Exception("Your account balance is not enough.")

    def run_first_basis(self, minimum_time=50):

        first_basis_counter = 0
        while True:
            current_number_of_bets = len(self._my_bets_info())

            if current_number_of_bets == 0:
                logging.info('Finding First Basis Game ...')
                # If bet is added successfully to a betslip
                if self.add_first_basis_games_to_betslip(minimum_time=minimum_time):
                    self._ten_percent_stake()
                    self.place_all_bets()

                    first_basis_counter += 1
                    logging.info('First basis counter at %d. Waiting for game to finish.', first_basis_counter)
                    time.sleep(1800)

                else:
                    continue

            else:

                logging.info('Waiting for current open bets to finish.')
                time.sleep(300)

            if first_basis_counter >= 7:
                break

        logging.info('Finished with First Basis. Heading to Second Basis Games.')

    def run_second_basis(self, minimum_time=0):

        second_basis_counter = 0
        while True:
            current_number_of_bets = len(self._my_bets_info())

            if current_number_of_bets == 0:
                logging.info('Finding Second Basis Game ...')

                # If bet is added successfully, increment the counter
                if self.add_second_basis_games_to_betslip(minimum_time=minimum_time):
                    self._ten_percent_stake()
                    self.place_all_bets()

                    second_basis_counter += 1
                    logging.info('Second basis counter at %d. Waiting for game to finish.')
                    time.sleep(3600)

                else:
                    continue

            else:
                logging.info('Waiting for current open bets to finish.')
                time.sleep(300)

            if second_basis_counter >= 2:
                break
