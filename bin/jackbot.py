#!/usr/bin/env python

import sys
import argparse
import os

# import all modules in jackbox package
package = "jackbox"
for module in os.listdir(f"{os.path.dirname(__file__)}/../{package}/"):
    if module == '__init__.py' or module == 'jackbox.py' or module[-3:] != '.py':
        continue
    __import__(f"{package}.{module[:-3]}", locals(), globals())
    del module


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Pull results from Jackbox game',
    )

    parser.add_argument(
        "-g", "--game_name",
        dest="game_name",
        help='''
        Game for which to retrieve results
        ex: Drawful2
            Quiplash2   
            drawful2
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

    args = parser.parse_args()

    if args.game_name is None:
        args.game_name = input("Enter game: ")

    if args.game_id is None:
        args.game_id = input("Enter game id: ")

    print(args)

    module_name = f"{package}.{args.game_name.lower()}"
    if module_name in sys.modules:
        method = "process_game"
        module = getattr(sys.modules[module_name], args.game_name.title())(game_id=args.game_id)
        if hasattr(module, method):
            try:
                getattr(module, method)()
            except Exception as e:
                sys.exit(e)
        else:
            sys.exit(f"ERROR: Module '{module_name}' does not have method '{method}'")
    else:
        sys.exit(f"ERROR: Module '{module_name}' is missing")


if __name__ == '__main__':
    main()
