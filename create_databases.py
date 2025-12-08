import sqlite3

with sqlite3.connect("data.db") as data:
    c = data.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Puzzles (
            puzzle_id INTEGER PRIMARY KEY,
            clues VARCHAR(81),
            difficulty INTEGER,
            mistakes INTEGER,
            hints INTEGER
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS PencilTypes (
            pencil_type_id INTEGER PRIMARY KEY,
            name VARCHAR(20),
            red INTEGER,
            green INTEGER,
            blue INTEGER,
            alpha INTEGER,
            strikethrough BOOL,
            strikethrough_red INTEGER NULL,
            strikethrough_green INTEGER NULL,
            strikethrough_blue INTEGER NULL,
            strikethrough_alpha INTEGER NULL
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ActionPencils (
            action_pencils_id INTEGER PRIMARY KEY,
            action_id INTEGER,
            pencil_type INTEGER,
            old_marks VARCHAR(9) NULL,
            new_marks VARCHAR(9) NULL,
            FOREIGN KEY(pencil_type) REFERENCES PencilTypes(pencil_type_id),
            FOREIGN KEY(action_id) REFERENCES Action(action_id)

        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Action (
            action_id INTEGER PRIMARY KEY,
            group_id INTEGER,
            puzzle_id INTEGER,
            row TINYINT,
            col TINYINT,
            old_value TINYINT,
            new_value TINYINT,
            unix_time FLOAT DEFAULT (unixepoch('subsec')),
            FOREIGN KEY(puzzle_id) REFERENCES Puzzles(puzzle_id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Completions (
            completion_id INTEGER PRIMARY KEY,
            puzzle_id INTEGER,
            FOREIGN KEY(puzzle_id) REFERENCES Puzzles(puzzle_id)
        )
        """
    )
