import numpy as np
import numpy.typing as npt
from sudoku import Board
import logging

# TODO: this whole codebase has way too many outdated comments filled with outdated information and deprecated code and this file is no exception. Remove some of them and add comments/docstrings that are actually accurate.


class Technique:
    # Needs to contain data about highlighting
    # For hints and cells several types of highlighting will be available
    # Advanced example (Finned Jelyfish) to help decide how to implement
    # "These cells are a Jelyfish, if you don't include this cell that shares a house with part of it. That means that either the Jellyfish is valid, or this cell is 7 so this cell which contradicts both cannot be 7"
    # Technique("Finned Jellyfish", [np.NDarray, "are a Jellyfish, if you don't include" np.NDarray, "that shares a {adjacency} with part of it. That means that either the Jellyfish is valid, or this cell is {num} so", np.NDarray, "which contradicts both cannot be {num}")
    # Message takes list[str | npt.NDArray] numpy arrays are coordinates and are converted to human readable coords.
    # Highlighting could be good, cell groups mentioned in the message can have different colours. Maybe {adjacency} can be bold or smth.
    # Might be better if it is just a string with stuff like %1 for 1st group and give a dictionary {1: some numpy array of coords}

    @staticmethod
    def set_message(message: list[dict[str, str | npt.NDArray[np.int8]]]):
        new_message: str = ""
        for part in message:
            try:
                tmp_value = part["value"]

                if isinstance(tmp_value, np.ndarray):
                    value: npt.NDArray[np.int8] = np.copy(tmp_value)
                    value += 1
                elif isinstance(tmp_value, str):
                    value: str = tmp_value
                elif isinstance(tmp_value, int):
                    value = tmp_value + 1
                elif isinstance(tmp_value, np.int8):
                    value = tmp_value + 1
                elif isinstance(tmp_value, np.int64):
                    # 64 bit int not ideal. Shouldn't need to be more than 8 but it isn't much of an issue.
                    value = tmp_value + 1
                else:
                    logging.warning(
                        f"Part of message has unknown type {type(tmp_value)}"
                    )
                    value = tmp_value

            except Exception as e:
                logging.error(
                    "Error with part of message\n" + repr(e)
                )  # TODO: make more descriptive and handle actual error instead
                break

            match part.get("type"):
                # TODO: I hate every part of this. Input is clunky and so is the way it's handled.
                # also needs different options for showing coords and stuff. (x, y) is not how sudoku coords are usually shown
                # rxcy would be better and may as well have chess coord notation as well
                case "text":
                    try:
                        new_message += value
                    except TypeError:
                        logging.error(
                            "Message part of type text contains non-string value"
                        )
                    except Exception as e:
                        logging.error(
                            "Error with interpreting text message part\n" + repr(e)
                        )
                case "coord":
                    try:

                        value.reshape(2)
                        new_message += f"Cell ({value[0]}, {value[1]})"
                    except Exception as e:
                        logging.error(
                            "Error with interpreting coord message part\n" + repr(e)
                        )

                case "coords":
                    try:
                        new_message += "Cells"
                        for coord in value:

                            new_message += f" ({coord[0]}, {coord[1]}),"
                    except Exception as e:
                        logging.error(
                            "Error with interpreting coords message part\n" + repr(e)
                        )
                case "num":
                    try:
                        if isinstance(value, np.ndarray):
                            value.reshape(1)
                            value = value[0]

                        new_message += "number " + str(value)
                    except Exception as e:
                        logging.error(
                            "Error with interpreting num message part\n" + repr(e)
                        )
                case "nums":
                    try:
                        new_message += "numbers"
                        for num in value:
                            new_message += " " + str(num.reshape(1)[0])
                    except Exception as e:
                        logging.error(
                            "Error with interpreting nums message part\n" + repr(e)
                        )
                case "candidates":
                    raise NotImplementedError("candidates don't work yet :(")
                case _:
                    raise NotImplementedError("Invalid type for part in message")
            new_message += " "

        return new_message

    def __init__(
        self, technique: str, message: list[dict[str, str | npt.NDArray[np.int8]]]
    ):
        self.technique = technique
        self.message = self.set_message(message)

    def add_cell(self, *coords: npt.NDArray[np.int8]): ...

    def remove_candidates(self, candidates: npt.NDArray[np.int8]): ...


class Human_Solver:
    def __init__(self, board: Board) -> None:
        self.candidates: npt.NDArray[np.bool] = board.get_candidates()  # 9x9x9
        # dimension 1 = number

    @staticmethod
    def _pretty_coords(row, column):
        return f"({row+1}, {column+1})"

    def _naked_singles(self):
        for coord in np.argwhere(np.add.reduce(self.candidates, axis=0) == 1):
            row, column = coord
            num = np.argwhere(self.candidates[:, row, column]).reshape(1)
            yield Technique(
                "Naked Single",
                [
                    {"type": "coord", "value": coord},
                    {"type": "text", "value": "is"},
                    {"type": "num", "value": num},
                    {
                        "type": "text",
                        "value": "because it is the only candidate for the cell.",
                    },
                ],  # TODO: this is kinda tedious to write but pretty versatile. Consider other options but this is ok. Could use a custom class instead of dict ig.
            )

    def _hidden_singles(self):
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }  # TODO: make this a class constant, and probably worth switching keys and values
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for func, adjacency in types.items():
                if (
                    np.count_nonzero(func((row, column)) & self.candidates[num]) == 1
                    and len(np.argwhere(self.candidates[:, row, column])) != 1
                ):

                    # TODO: also check for naked singles, honestly naked varieties seem like they tend to be different enough that it might make more sense to have in seperate functions. It would also make checking which technique is easiest easier as only the method used needs to be considered instead of the specifics of how the technique was applied.

                    x = Technique(
                        "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
                        # TODO: check if comment above is actually right.
                        [
                            {
                                "type": "coord",
                                "value": np.array([row, column], dtype=np.int8),
                            },
                            {"type": "text", "value": "is"},
                            {"type": "num", "value": num},
                            {
                                "type": "text",
                                "value": f"because there are no others in the {adjacency}",
                            },
                        ],
                        # f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}",
                    )
                    x.add_cell(coord)
                    #                     print(
                    #                         f"""
                    # Technique(
                    #                         "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
                    #                         f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}",
                    #                     ).add_cell({coord})
                    #
                    #                           """
                    #                     )
                    yield x  # Maybe yield instead but this is prob best, only getting first one. Could make testing harder tho because if I reimplement it in a different way it could find a different single instead and which single to find really doesn't matter. Yielding could maybe give more flexibility with a hint system, allowing the user to see several examples.

    def _naked_pairs(self):
        # TODO: it can give the same pair twice because it checks coordinates of both items. Fix this. Also a problem for hidden pairs. This isn't actually a problem, all the hints are still correct its just some are redundant. It would be quite nice for the hint to say stuff like it is a pair along the box and the column or whatever.
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }

        for coord in np.argwhere(np.add.reduce(self.candidates, axis=0) == 2):
            row, column = coord
            nums = np.argwhere(self.candidates[:, row, column])
            for func, adjacency in types.items():

                coords = np.argwhere(
                    np.logical_and.reduce(
                        func((row, column))
                        & self.candidates[nums]
                        & (np.add.reduce(self.candidates, axis=0) == 2),
                    ).reshape(9, 9)
                )
                if len(coords) != 2:
                    continue

                # Should be the same as checking the second coord. I think it is guarenteed but worth double checking.

                nums = np.argwhere(self.candidates[:, coords[0, 0], coords[0, 1]])

                yield Technique(
                    "Naked Pair",
                    [
                        {"type": "coords", "value": coords},
                        {"type": "nums", "value": nums},
                        {"type": "text", "value": f"along {adjacency}"},
                    ],
                )

    def _hidden_pairs(self):
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }
        for coord in np.argwhere(self.candidates):
            num, row, column = coord

            # Hidden pairs
            for func, adjacency in types.items():
                if (
                    np.count_nonzero(func((row, column)) & self.candidates[num]) == 2
                ):  # TODO: some of these snippets will appear in lots of techniques, maybe make some helper functions
                    coords = np.argwhere(func((row, column)) & self.candidates[num])
                    if len(coords) != 2:
                        continue

                    # Num is always increasing so only check against higher nums
                    # There is probably a better way of doing this with some numpy tricks
                    for i in range(num + 1, 9):
                        if np.array_equal(
                            np.argwhere(func((row, column)) & self.candidates[i]),
                            coords,
                        ):

                            x = Technique(
                                "Hidden Pair",
                                [
                                    {"type": "coords", "value": coords},
                                    {
                                        "type": "text",
                                        "value": "are the only cells that can be",
                                    },
                                    {"type": "num", "value": num},
                                    {"type": "text", "value": "or"},
                                    {"type": "num", "value": i},
                                    {
                                        "type": "text",
                                        "value": f"in their {adjacency}, so we can remove all other candidates from them.",
                                    },
                                ],
                            )
                            # TODO: explanation incomplete and I don't like they way it uses way too many dictionaries. Make message input to Technique easier.
                            yield x

    def hint(self):
        types = [
            self._naked_singles,
            self._hidden_singles,
            self._naked_pairs,
            self._hidden_pairs,
        ]
        # Maybe doing this async in some way could help. But because if only returns the easiest technique it might not be the easiest to do.
        # Could potentially start looking for all types at the same time and await them in order of easiest to hardest and return first non-null.
        # As long as I keep writing the techniques efficiently, using numpy as much as possible it shouldn't really matter if it is async or not but maybe it would with some of the more advanced techniques, like if I do 3d medusa chain analysis.
        for technique in types:
            for y in technique():
                if y:
                    yield y


if __name__ == "__main__":
    board = Board(
        ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
        # "................................................................................1"
        # "..............................................................................321"
    )

    board.auto_normal()

    human: Human_Solver = Human_Solver(board)

    for technique in human._hidden_singles():
        print("found")

    # TODO: tests needed for all techniques. This is probably a higher priority than adding more techniques. Testing properly is tricky because there may be several valid ways to apply the technique and which one gets used really doesn't matter.
    # techniques are now yielded so tests should check all of them. Although there could maybe be some issues like if a hidden single was hidden single for box and column would that be 1 or 2 techniques.
