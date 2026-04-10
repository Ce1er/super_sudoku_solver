import argparse


def main():
    parser = argparse.ArgumentParser(prog="super_sudoku_solver")

    # If subparser used set entry_point to subparser's name
    subparsers = parser.add_subparsers(title="entry points", dest="entry_point")

    # Parser to use when first arg is save_manager (or alias)
    save_manager_parser = subparsers.add_parser(
        name="save_manager",
        description="Create, delete or modify saved puzzles.",
        aliases=["sm"],
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
        "--reset-puzzle-data",
        action="store_true",
        help="Revert all puzzles to their starting state.",
    )
    save_manager_parser.add_argument(
        "--reset-all-data",
        action="store_true",
        help="Delete all save data.",
    )

    args = parser.parse_args()

    # Determine entrypoint based on subparser used
    # Fallback to gui if no subparser used
    match args.entry_point:
        case "save_manager":
            import super_sudoku_solver.save_manager as save_manager

            save_manager.main(args)
        case _:
            import super_sudoku_solver.gui as gui

            gui.main()
