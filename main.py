from PySide6.QtWidgets import (
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QKeySequence, QPainter, QPen, QBrush, QFont, QColor
from PySide6.QtCore import QKeyCombination, QRectF, Qt
import sys
import numpy as np
import numpy.typing as npt
from typing import Callable, Optional, Self
from itertools import product
from functools import wraps

# The latter is for type hints. It should never be used directly and I should enforce this.
from settings import settings, Settings

from sudoku import Board as BoardData
from utils import get_first

# from human_solver import HumanSolver, Technique
from human_solver import Technique, Action
import techniques

from save_manager import Puzzles

from custom_types import Coord, Candidates, Cells, Candidates, CellCandidates
from custom_types import Cell as CellT

from utils import text_hints


# TODO: pass in font so it is customisable
# Also all these colours and sizes and stuff is getting excessive
# Should be part of settings
class Cell(QGraphicsItem):
    def __init__(
        self,
        coord: CellT,
        candidates: Candidates,
        clue: bool,
        settings: Settings,
    ) -> None:
        """
        Args:
            coord: [row, column, value] (all 0-8 inclusive but value can also be -1 to indicate no value)
            candidates: 1d boolean array where candidates[n] == True means number n+1 can be in cell
        """
        super().__init__()
        self.row: int = coord[0]
        self.col: int = coord[1]
        self.value: int = -1 if coord[2] == -1 else coord[2] + 1
        self.candidates: npt.NDArray[np.bool] = candidates
        tmp = []
        for colour in self.candidates:
            tmp.append(QPen(settings.colours.candidate))
        self.candidate_pens = tmp
        self.highlight: Optional[int] = None
        self.size: int = settings.sizes.cell
        self.clue: bool = clue

        self.border_colour = settings.colours.border
        self.background_colour = settings.colours.background
        self.highlight_colour = settings.colours.special_candidate
        self.clue_pen = QPen(
            settings.colours.clue,
        )
        self.guess_pen = QPen(
            settings.colours.guess,
        )
        # TODO: improve how I set pen

        self.border_size = settings.sizes.border

        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.highlighted = False

    def highlight_candidates(self, candidates: list[int], colour: QColor) -> None:
        for candidate in candidates:
            self.candidate_pens[candidate] = QPen(colour)

    def boundingRect(self):
        return QRectF(0, 0, self.size, self.size)

    def paint(self, painter, option, widget):
        # TODO: IMPORTANT
        # Make this work with highlights
        if self.highlight:
            painter.fillRect(
                self.boundingRect(),
                QBrush(self.highlight_colour),
            )
        else:
            painter.fillRect(self.boundingRect(), QBrush(settings.colours.background))

        pen = QPen(self.border_colour, self.border_size)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        if self.value != -1:
            if self.clue:
                painter.setPen(self.clue_pen)
                painter.setFont(QFont("Arial", int(self.size * 0.5), QFont.Bold))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.value))
            else:
                painter.setPen(self.guess_pen)
                painter.setFont(QFont("Arial", int(self.size * 0.5)))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.value))

        elif np.count_nonzero(self.candidates) != 0:
            painter.setFont(QFont("Arial", int(self.size * 0.2)))
            width = self.size / 3
            height = self.size / 3
            for i in range(9):
                if self.candidates[i]:
                    painter.setPen(self.candidate_pens[i])
                    row = i // 3
                    column = i % 3
                    x = column * width
                    y = row * height
                    painter.drawText(
                        QRectF(x, y, width, height), Qt.AlignCenter, str(i + 1)
                    )

    def mousePressEvent(self, event) -> None:
        scene = self.scene()
        if hasattr(scene, "cell_clicked"):
            scene.cell_clicked(self)
        event.accept()

    def set_value(self, value: int):
        self.value = -1 if value == -1 else value + 1
        if value != -1:
            self.candidates = np.full([9], False)
        self.update()

    def set_candidates(self, value: npt.NDArray[np.bool]):
        self.candidates = value
        self.update()

    def set_highlighted(self, value: bool):
        self.highlighted = value
        self.update()


class HintBox(QGraphicsItem):
    def __init__(
        self,
        technique: Technique,
        settings: Settings,
    ):  # TODO: take colours and stuff as well. Probably should implement Action before trying to get cell highlighting working but the message box part can be done at any time.
        super().__init__()

        # TODO: Width and height set based on text length.

        self.technique = technique

        self.settings = settings

        self.text_size = settings.sizes.text
        self.width = len(technique.message) * settings.sizes.text
        self.height = settings.sizes.text * 2

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(settings.colours.background))
        pen = QPen(self.settings.colours.border, self.settings.sizes.border)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        painter.setFont(QFont("Arial", self.text_size))
        # TODO: handle special text highlighting and stuff.
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.technique.message)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent, /) -> None:
        """
        On LMB apply action
        """
        # TODO: somehow this action needs to be passed back up to Board
        # and it should handle it by applying the action
        scene = self.scene()
        scene.apply_action(self.technique.action)
        event.accept()


class Board(QGraphicsScene):
    def _auto_note(func: Callable[[Self], None]) -> Callable[[Self], None]:
        """
        Decorator to run self.auto_note() after execution if desired
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            if self.do_auto_note:
                self.auto_note()

        return wrapper

    @_auto_note
    def __init__(
        self,
        data: BoardData,
        settings: Settings,
    ):
        super().__init__()
        self.data = data

        self.selected_cell = None
        self.cells: list[list[Cell]] = []

        self.settings = settings
        self.do_auto_note = settings.gameplay.auto_note

        if settings.gameplay.start_full:
            self.data.all_normal()

        solution = None
        for n, value in enumerate(self.data.solve()):
            if n > 1:
                raise ValueError("Board has multiple solutions")

            solution = value
        if solution is None:
            raise ValueError("Board has no solution")
        self.solution = solution

        self.hint = None
        # TODO: hint should be tracked so it can be handled better
        # hint should be printed in paint_board instead. I think?
        # There should be a button somewhere that appears only when a hint is active
        # This button will apply the hint
        # The hint should be cleared when it is applied or when the user applies it themselves
        # Also needs proper highlighting
        # I can either keep a hintbox at all times and toggle its visibility based on if there is a hint
        # Or I can delete it when there isn't and make a new one.

        self.paint_board()

    def paint_board(self):
        print("pb", text_hints(self.data.candidates))
        x = -1
        for row, col in product(range(9), repeat=2):
            if row > x:
                x = row
                self.cells.append([])
            # for coord in self.data.get_cells():
            for coord in np.argwhere(self.data.cells != -1):
                if coord[0] == row and coord[1] == col:
                    value = self.data.cells[row, col]
                    break
            else:
                value = -1

            cell = Cell(
                np.array([row, col, value]),
                self.data.candidates[:, row, col],
                self.data.is_clue(np.array([row, col])),
                self.settings,
            )
            cell.setPos(col * self.settings.sizes.cell, row * self.settings.sizes.cell)
            self.addItem(cell)
            # TODO: Use QGraphicsItemGroup instead?
            self.cells[-1].append(cell)

        pen = QPen(self.settings.colours.big_border, self.settings.sizes.big_border)
        for i in range(10):
            width = self.settings.sizes.cell * 9
            x = i * self.settings.sizes.cell
            self.addLine(
                x,
                0,
                x,
                width,
                (
                    pen
                    if i % 3 == 0
                    else QPen(self.settings.colours.border, self.settings.sizes.border)
                ),
            )

            y = i * self.settings.sizes.cell
            self.addLine(
                0,
                y,
                width,
                y,
                (
                    pen
                    if i % 3 == 0
                    else QPen(self.settings.colours.border, self.settings.sizes.border)
                ),
            )

    def update_candidates(self):
        """
        Updates candidates and cells
        """
        print("uc", text_hints(self.data.candidates))
        for row, col in product(range(9), repeat=2):
            self.cells[row][col].set_candidates((self.data.candidates[:, row, col]))
            self.cells[row][col].set_value(self.data.cells[row, col])

    def cell_clicked(self, cell: Cell):
        if self.selected_cell:
            self.selected_cell.set_highlighted(False)
        self.selected_cell = cell
        cell.set_highlighted(True)

    def show_hint(self):
        def get_techniques():
            for technique in techniques.TECHNIQUES:
                # print(technique)
                x = technique(
                    self.data.candidates,
                    self.data.clues,
                    self.data.guesses,
                )
                yield from x.find()

        # FIXME:the hint system can't see guesses. Only initial clues. I think the candidates also aren't being updated properly for guesses.

        # TODO: check action is non-null

        # TODO: a way of getting other ones
        technique = get_first(get_techniques())
        print(technique)
        if technique is None:
            return -1
        print("hint")
        print(technique.message)
        action = technique.action
        print(action.cells)
        print(action.candidates)

        if self.hint is not None:
            self.removeItem(self.hint)

        hint = HintBox(technique, self.settings)
        hint.setPos(self.settings.sizes.cell * 9 + 5, 0)
        self.hint = hint
        self.addItem(hint)

        action: Action = technique.action
        cells = action.cells
        candidates = action.candidates

        for cell in np.argwhere(cells):
            print(cell)

        print(self.cells)
        for candidate in np.argwhere(candidates):
            num, row, col = candidate
            print(num, row, col)
            print(type(row))

            # TODO: maybe make self.cells a numpy array of objects. Got so confused here why np style indexing didn't work.
            self.cells[(row)][(col)].highlight_candidates([num], "a50510")

    def remove_cell(self):
        """
        Remove the value for the currently selected cell.
        """
        # Do not let user remove clues
        if self.selected_cell.clue:
            return

        self.selected_cell.set_value(-1)

    @_auto_note
    def add_cell(self, value: int):
        """
        Sets the value at the currently selected cell
        Args:
            value: value to set the cell. Between 0 and 8 inclusive.
        """
        if self.solution[self.selected_cell.row, self.selected_cell.col] != value:
            # TODO: dialog to show this
            print("Incorrect")
            return

        self.selected_cell.set_value(value)
        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[
            self.selected_cell.row,
            self.selected_cell.col,
        ] = (
            self.selected_cell.value - 1
        )

        self.data.add_cells(new_cells)

    def auto_note(self):
        """
        Remove candidates if they are adjacent to a cell with their value.
        """
        self.data.auto_normal()
        self.update_candidates()

    def apply_action(self, action: Action):
        """
        Apply the current hint to the board
        """
        # TODO: somewhere I need to check if the action is actually valid
        # This should always be the case but a failsafe is worth adding
        self.data.apply_action(action)
        self.removeItem(self.hint)
        self.hint = None
        self.paint_board()

    def apply_hint(self):
        if self.hint is None:
            return

        self.apply_action(self.hint.technique.action)

    def solve(self):
        """
        Solve the puzzle automatically
        """
        self.data.auto_solve()
        self.update_candidates()

    def keyPressEvent(self, event) -> None:
        if not self.selected_cell:
            return

        key = Qt.Key(event.key())
        mods = event.modifiers()
        seq = QKeySequence(QKeyCombination(mods, key))
        binds = self.settings.keybinds

        number_keys = [i for s in binds.numbers.values() for i in s]
        if seq in number_keys:
            value = None
            for k, v in binds.numbers.items():
                if key in v:
                    value = k - 1
                    break

            assert value is not None
            self.add_cell(value)

        elif seq in binds.remove:
            # FIXME: doesn't persist after auto normal
            self.remove_cell()
        elif seq in binds.auto_note:
            # FIXME: doesn't do anything when used after the user inputs a guess
            self.auto_note()
        elif seq in binds.solve:
            self.solve()
        elif seq in binds.hint:
            self.show_hint()
        elif seq in binds.apply_hint:
            self.apply_hint()


def main():
    app = QApplication(sys.argv)
    puzzles = Puzzles()
    for name, puzzle in puzzles.puzzle_map.items():
        print("a", name, puzzle)
        p = puzzle
        if name == "hard_1":
            break

    scene = Board(
        BoardData(
            # "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
            # "123456789..............................................................1........."
            # ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
            # "1.....569492.561.8.561.924...964.8.1.64.1....218.356.4.4.5...169.5.614.2621.....5"
            p
        ),
        settings,
    )
    view = QGraphicsView(scene)
    view.setFocusPolicy(Qt.StrongFocus)
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# TODO: sudoku board needs buttons as alternatives to all key binds
# Also needs a button to go to main menu
# Main menu should have a way to select puzzle
