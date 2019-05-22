import time
import datetime

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

            print("<[{}]> Stake set for this betslip is {}".format(str(datetime.datetime.now()), self.current_stake))

            return self.current_stake

        else:
            Exception("Your account balance is not enough.")

    def run_first_basis(self, minimum_time):

        first_basis_counter = 0
        while True:
            current_number_of_bets = len(self._my_bets_info())

            if current_number_of_bets == 0:
                print("<[{}]> Finding First Basis Game ... ".format(str(datetime.datetime.now())))
                # If bet is added successfully to a betslip
                if self.add_first_basis_games_to_betslip(minimum_time=minimum_time):
                    self._ten_percent_stake()
                    self.place_all_bets()

                    first_basis_counter += 1
                    print("<[{}]> First basis counter at {}. Waiting for game to finish ... ".
                          format(str(datetime.datetime.now()), first_basis_counter))
                    time.sleep(1800)

                else:
                    continue

            else:
                print("<[{}]> Waiting for current open bets to finish ... ".
                      format(str(datetime.datetime.now())))
                time.sleep(300)

            if first_basis_counter >= 7:
                break

        print("\n\n\n------------------------------------------------------------------------------------------")
        print("<[{}]> Finished with First Basis. Heading to Second Basis Games".format(
            str(datetime.datetime.now())
        ))
        print("------------------------------------------------------------------------------------------------\n\n\n")

    def run_second_basis(self, minimum_time):

        second_basis_counter = 0
        while True:
            current_number_of_bets = len(self._my_bets_info())

            if current_number_of_bets == 0:
                print("<[{}]> Finding Second Basis Game ... ".format(str(datetime.datetime.now())))

                # If bet is added successfully, increment the counter
                if self.add_second_basis_games_to_betslip(minimum_time=minimum_time):
                    self._ten_percent_stake()
                    self.place_all_bets()

                    second_basis_counter += 1
                    print("<[{}]> Second basis counter at {}. Waiting for game to finish ... ".
                          format(str(datetime.datetime.now()), second_basis_counter))
                    time.sleep(3600)

                else:
                    continue

            else:
                print("<[{}]> Waiting for current open bets to finish ... ".
                      format(str(datetime.datetime.now())))
                time.sleep(300)

            if second_basis_counter >= 2:
                break

        print("Finished today's games!!!!!!!!")
        exit()
