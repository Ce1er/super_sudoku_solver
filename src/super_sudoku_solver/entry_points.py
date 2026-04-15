import argparse


def main():
    parser = argparse.ArgumentParser(prog="super_sudoku_solver")

    # If subparser used set entry_point to subparser's name. Otherwise leave as None.
    subparsers = parser.add_subparsers(title="entry points", dest="entry_point")

    save_manager_names = ("save_manager", "sm")

    # Use this subparser when first arg is in `save_manager_names`
    save_manager_parser = subparsers.add_parser(
        name=save_manager_names[0],
        description="Create, delete or modify saved puzzles.",
        aliases=save_manager_names[1:],
    )
    save_manager_parser.add_argument(
        "-d",
        "--delete",
        nargs=1,
        action="append",
        metavar=("UUID"),
        help="Delete a puzzle",
    )
    save_manager_parser.add_argument(
        "-u",
        "--update",
        nargs=2,
        action="append",
        metavar=("UUID", "DIFFICULTY"),
        help="Change a puzzle's difficulty",
    )
    save_manager_parser.add_argument(
        "-a",
        "--add",
        nargs=2,
        action="append",
        metavar=("CLUES", "DIFFICULTY"),
        help="Add a puzzle",
    )
    save_manager_parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List installed puzzles.",
    )
    save_manager_parser.add_argument(
        "--reset-puzzle-data",
        action="store_true",
        help="Revert all puzzles to their starting state.",
    )
    save_manager_parser.add_argument(
        "--reset-all-data",
        action="store_true",
        help="Delete all save data.",
    )
    save_manager_parser.add_argument(
        "--restore-default-puzzles",
        action="store_true",
        help="Restore default puzzles.",
    )
    save_manager_parser.add_argument(
        "--restore-default-config",
        action="store_true",
        help="Restore default config file.",
    )

    args = parser.parse_args()

    # Determine entrypoint based on subparser used
    # Fallback to gui if no subparser used
    if args.entry_point in save_manager_names:
        import super_sudoku_solver.save_manager as save_manager

        save_manager.main(args)
    else:
        import super_sudoku_solver.gui as gui

        gui.main()
