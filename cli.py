from sudoku import Board
from human_solver import Human_Solver
from utils import get_first, text_board
import os

if __name__ == "__main__":
    os.system("clear")  # TODO: don't assume system is UNIX based
    while True:
        try:
            board = Board(input("Enter cells"))
            break
        except Exception as e:
            print(repr(e))
    print(text_board(board.cells.cells))  # TODO: access with getters instead
    while True:
        print(
            """
        Choose an option:
        s: solve
        h: hint
        c: clear
        """
        )
        choice = input("")
        match choice.lower().strip():
            case "s":
                print(text_board(get_first(board.solve())))
            case "h":
                board.auto_normal()
                human = Human_Solver(board)
                for hint in human.hint():
                    print(hint.technique)
                    print(hint.message)
                    print("\n")

            case "c":
                os.system("clear")
                print(
                    text_board(board.cells.cells)
                )  # TODO: access with getters instead
            case _:
                print("Invalid choice")
