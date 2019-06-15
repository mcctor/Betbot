import argparse

from Odi.odibot import Odibot

if __name__ == '__main__':

    parse = argparse.ArgumentParser(
        description='A script meant for automated betting with https://odibets.com. The strategy it'
                    ' uses is highlighted in the README.md.'
    )

    parse.add_argument('phone_number', help='Your phone number as registered with https://odibet.com')
    parse.add_argument('password', help='Your odibets password.')
    parse.add_argument('stake', type=int, help='The maximum stake figure this script will ever work with.')

    # parse the two arguments.
    args = parse.parse_args()

    # Instantiate Odibot Class by giving phone and password arguments.
    bet_bot = Odibot(phone_number=args.phone_number, password=args.password, stake_figure=args.stake)

    # Execute the first basis of the betting strategy.
    bet_bot.run_first_basis()

    # Execute the second basis of the betting strategy.
    bet_bot.run_second_basis()
