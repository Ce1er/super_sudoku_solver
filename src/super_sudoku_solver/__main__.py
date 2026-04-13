"""
File to allow module to be ran with `python -m super_sudoku_solver` as 
alternative to gui-script generated after installation.
"""

import super_sudoku_solver.entry_points as entry_points

# __main__.py files typically don't check __name__ as they can't be imported
# https://docs.python.org/3/library/__main__.html#main-py-in-python-packages
entry_points.main()
