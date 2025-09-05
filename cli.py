from sudoku import Board
from human_solver import Human_Solver
from utils import get_first, text_board, text_hints
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
        a: show all hints
        n: show candidate notes
        g: enter a number
        c: clear
        """
        )
        choice = input("")
        match choice.lower().strip():
            case "s":
                solved = False
                for solution in board.solve():
                    solved = True
                    print(text_board(solution))

                if not solved:
                    print("Board is in an unsolvable state")

            case "a":
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
            case "n":
                board.auto_normal()
                print(text_hints(board.hints["normal"].get_hints()))
            case "g":
                while True:
                    try:
                        row = int(input("Enter row number: ")) - 1
                        if row not in range(9):
                            raise ValueError
                        break
                    except Exception as e:
                        print("Invalid number")

                while True:
                    try:
                        column = int(input("Enter column number: ")) - 1
                        if column not in range(9):
                            raise ValueError
                        break
                    except Exception as e:
                        print("Invalid number")

                while True:
                    try:
                        num = int(input("Enter number: "))
                        if num not in range(1, 10):
                            raise ValueError
                        break
                    except Exception as e:
                        print("Invalid number")

                board.cells.add_cell((row, column), num)
                print(text_board(board.cells.cells))
            case _:
                print("Invalid choice")
