from Odi.odibot import Odibot

if __name__ == '__main__':
    # Instantiate Odibot Class by giving phone and password arguments.
    bet_bot = Odibot(phone_number="0740779569", password="Abacadabra01", stake_figure=50)

    # Execute the first basis of the betting strategy.
    bet_bot.run_first_basis()

    # Execute the second basis of the betting strategy.
    bet_bot.run_second_basis()
