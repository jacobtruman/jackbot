#!/usr/bin/env python

import sys
import argparse
import os

from jackbox import Jackbox

# import all modules in jackbox package
PACKAGE = "jackbox"
modules_names = []
for module in os.listdir(f"{os.path.dirname(__file__)}/../{PACKAGE}/"):
    if module == '__init__.py' or module == 'jackbox.py' or module[-3:] != '.py':
        continue
    modules_names.append(module[:-3])
    __import__(f"{PACKAGE}.{module[:-3]}", locals(), globals())
    del module


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Pull results from Jackbox game',
    )

    parser.add_argument(
        "-g", "--game_name",
        dest="game_name",
        help=f'''
        Game for which to retrieve results
        ex: {", ".join(modules_names)}
        '''
    )

    parser.add_argument(
        "-i", "--game_id",
        dest="game_id",
        help='''
        ID of the game for which to retrieve results
        ex: http://games.jackbox.tv/artifact/Quiplash2Game/fa52a821368421e960dff1b6fa1dcf07/
            fa52a821368421e960dff1b6fa1dcf07
            games.jackbox.tv/artifact/DrawfulGame/195dd2b39eab8af9bb08c1a090723ef9
        '''
    )

    parser.add_argument(
        "-u", "--game_url",
        dest="game_url",
        help='''
            Url of the game for which to retrieve results
            ex: http://games.jackbox.tv/artifact/Quiplash2Game/fa52a821368421e960dff1b6fa1dcf07/
            '''
    )

    parser.add_argument(
        "-a", "--api_account",
        dest="api_account",
        default="dev",
        help='API account key as defined in ~/.config/jackbot/config.json. Default dev'
    )

    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        dest='dry_run',
        help='Purge successfully converted source files',
    )

    args = parser.parse_args()

    if args.game_url is None:
        if args.game_name is None:
            args.game_name = input("Enter game: ")

        if args.game_id is None:
            args.game_id = input("Enter game id: ")
    else:
        args.game_name, args.game_id = Jackbox.parse_game_url(args.game_url)

    print(args)

    module_name = f"{PACKAGE}.{args.game_name.lower()}"
    if module_name in sys.modules:
        method = "process_game"
        _module = getattr(sys.modules[module_name], args.game_name.title())(
            game_id=args.game_id,
            api_account=args.api_account,
            dry_run=args.dry_run
        )
        if hasattr(_module, method):
            try:
                getattr(_module, method)()
            except Exception as exc:  # pylint: disable=broad-except
                raise exc
        else:
            sys.exit(f"ERROR: Module '{module_name}' does not have method '{method}'")
    else:
        sys.exit(f"ERROR: Module '{module_name}' is missing")


if __name__ == '__main__':
    main()
