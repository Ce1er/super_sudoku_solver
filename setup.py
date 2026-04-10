from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip()]


setup(
    name="super_sudoku_solver",
    version="1.0.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "gui_scripts": ["super-sudoku-solver = super_sudoku_solver.__main__:main"]
    },
)
