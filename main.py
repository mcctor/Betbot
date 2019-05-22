from Odi.odibot import Odibot

if __name__ == '__main__':
    bet_bot = Odibot(phone_number="0740779569", password="Abacadabra01", stake_figure=50)
    bet_bot.run_first_basis(minimum_time=50)
    bet_bot.run_second_basis(minimum_time=0)
