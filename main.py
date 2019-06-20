import os

from Odi.odibot import Odibot

if __name__ == '__main__':

    # run the loop forever.
    while True:

        # Instantiate Odibot Class by giving phone and password arguments.
        bet_bot = Odibot(
            phone_number=os.environ['phone_number'],
            password=os.environ['password'],
            stake_figure=os.environ['stake_figure']
        )

        # Execute the first basis of the betting strategy.
        bet_bot.run_first_basis()

        # Execute the second basis of the betting strategy.
        bet_bot.run_second_basis()
