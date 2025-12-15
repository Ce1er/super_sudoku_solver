import sqlite3

with sqlite3.connect("data.db") as data:
    c = data.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Puzzles (
            puzzle_id INTEGER PRIMARY KEY,
            clues TEXT,
            difficulty INTEGER
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS PencilTypes (
            pencil_type_id INTEGER PRIMARY KEY,
            name TEXT,
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
            old_marks TEXT NULL,
            new_marks TEXT NULL,
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
            row INTEGER,
            col INTEGER,
            old_value INTEGER,
            new_value INTEGER,
            unix_time REAL DEFAULT (unixepoch('subsec')),
            by_user BOOL,
            technique_name TEXT,
            FOREIGN KEY(puzzle_id) REFERENCES Puzzles(puzzle_id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS Completion (
            completion_id INTEGER PRIMARY KEY,
            puzzle_id INTEGER,
            time_taken REAL,
            mistakes INTEGER,
            hints INTEGER,
            FOREIGN KEY(puzzle_id) REFERENCES Puzzles(puzzle_id)
        )
        """
    )
