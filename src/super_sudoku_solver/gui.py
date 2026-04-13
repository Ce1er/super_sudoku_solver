from typing import Callable, Optional, Self

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsProxyWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QLabel,
    QListWidget,
    QPushButton,
    QCheckBox,
)
from PySide6.QtGui import (
    QKeySequence,
    QPen,
    QBrush,
    QFont,
    QColor,
    QTextDocument,
)
from PySide6.QtCore import QKeyCombination, QRectF, Qt, Signal, QTimer, QObject

import sys
import logging

from functools import wraps,  partial
from itertools import product, count, repeat
from random import choice
from html import escape

import super_sudoku_solver.np_candidates as npc
import numpy as np
import numpy.typing as npt

from super_sudoku_solver.sudoku import Board as BoardData
from super_sudoku_solver.sudoku import InvalidBoard
from super_sudoku_solver.save_manager import Puzzles

from super_sudoku_solver.techniques import TECHNIQUES
import super_sudoku_solver.human_solver as human_solver

from super_sudoku_solver.settings import settings, Settings

from super_sudoku_solver.human_solver import (
    MessageCoords,
    MessageText,
    Technique,
    Action,
    MessageNum,
)
from super_sudoku_solver.custom_types import Candidates, Coords
from super_sudoku_solver.custom_types import Cell as CellT



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
        self.settings = settings
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

        self._highlight_lock = False

    def highlight_lock(self):
        print("locked")
        self._highlight_lock = True

    def highlight_unlock(self):
        print("unlocked")
        self._highlight_lock = False

    def highlight_background(self, colour):
        """
        Change background colour for the cell.
        Args:
            colour: None to reset to default. Anything QColor can interpret to set new colour.
        """
        if self._highlight_lock:
            return

        if colour is None:
            self.highlighted = False
            new = self.settings.colours.background
        else:
            self.highlighted = True
            new = QColor(colour)

        # QColor doesn't raise an error for all invalid inputs
        if not new.isValid():
            raise ValueError("Could not interpret colour for cell background")

        self.background_colour = new
        self.update()

    def highlight_candidates(self, candidates: list[int], colour: QColor) -> None:
        for candidate in candidates:
            self.candidate_pens[candidate] = QPen(colour)

    def boundingRect(self):
        return QRectF(0, 0, self.size, self.size)

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(self.background_colour))

        pen = QPen(self.border_colour, self.border_size)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        # Paint value
        if self.value != -1:
            if self.clue:
                painter.setPen(self.clue_pen)
                painter.setFont(QFont("Arial", int(self.size * 0.5), QFont.Bold))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.value))
            else:
                painter.setPen(self.guess_pen)
                painter.setFont(QFont("Arial", int(self.size * 0.5)))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.value))

        # Paint candidates
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

    # def set_highlighted(self, value: bool):
    #     self.highlighted = value
    #     self.update(self.boundingRect())


# This class is mostly a QGraphicsItem, QObject is only needed for Signal
class HintBox(QGraphicsItem, QObject):
    # Coords or Coord of cells to highlight
    highlight_cells = Signal(object)
    highlight_candidates = Signal(object)

    def __init__(
        self,
        technique: Technique,
        settings: Settings,
    ):  # TODO: take colours and stuff as well. Probably should implement Action before trying to get cell highlighting working but the message box part can be done at any time.

        QObject.__init__(self)
        QGraphicsItem.__init__(self)

        # TODO: Width and height set based on text length.
        # Also need to handle multiline text.
        # Split into lines based on the width.
        # Maybe look at redbot formatting pagify

        self.technique = technique

        self.highlight_cells_calls = []

        # TODO: move to settings
        colours = {1: "#a50510", 2: "#aabb00", 3: "#0000bb"}
        html = "<b>" + escape(self.technique.technique) + "</b><br>"
        for message_part in self.technique.message_parts:
            if message_part.highlight is not None:
                html += f'<span style="background-color: {colours[message_part.highlight]};"><b>{escape(message_part.text)}</b></span>'

                # if isinstance(message_part, human_solver.MessageCoord):
                #     self.highlight_cells_calls.append(
                #         (message_part.coord, colours[message_part.highlight])
                #     )

                if isinstance(message_part, human_solver.MessageCoords):
                    self.highlight_cells_calls.append(
                        (message_part.coords, colours[message_part.highlight])
                    )
            else:
                if isinstance(message_part, human_solver.MessageNum) or isinstance(
                    message_part, human_solver.MessageNums
                ):
                    html += "<b>" + escape(message_part.text) + "</b>"
                else:
                    html += escape(message_part.text)

            html += " "
            # TODO: check if resulting html has trailing space after it is loaded

        self.width = 200
        self.text = QTextDocument()
        self.text.setHtml(html)
        self.text.setTextWidth(self.width)
        self.settings = settings
        self.height = self.text.size().height()

        self.text_size = settings.sizes.text

        print(self, self.text, self.width, self.height)

    def send_highlights(self):
        for call in self.highlight_cells_calls:
            print(call)
            self.highlight_cells.emit(call)

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(settings.colours.background))
        pen = QPen(self.settings.colours.border, self.settings.sizes.border)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        painter.setFont(QFont("Arial", self.text_size))
        # TODO: handle special text highlighting and stuff.
        # painter.drawText(self.boundingRect(), Qt.AlignCenter, self.text)

        painter.save()
        # painter.translate(20,40)
        self.text.drawContents(painter)
        painter.restore

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent, /) -> None:
        """
        On LMB apply action
        """
        # TODO: somehow this action needs to be passed back up to Board
        # and it should handle it by applying the action
        scene = self.scene()
        scene.apply_action(self.technique.action)
        event.accept()


class PuzzleSelector(QListWidget):
    data = Signal(BoardData)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

        self.puzzles = Puzzles().puzzle_map
        names = self.puzzles.keys()
        print(list(names))
        self.addItems(list(self.puzzles.keys()))

        self.itemClicked.connect(self.puzzle_selected)

        # self.data = Signal(BoardData)

    def puzzle_selected(self, item):
        print("Selected:", item.text())
        # scene = self.scene()
        # scene.set_puzzle(self.puzzles[item.text()])
        self.data.emit((self.puzzles[item.text()]))
        # TODO: use signals in the other classes


class ErrorBox(QLabel):
    """
    To show the user warning messages
    These warnings aren't fatal but are useful for the user
    """

    # TODO: I prefer HintBox
    # Make a base class for that and have both HintBox and ErrorBox inherit from it

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings


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

    def _update_candidates(func: Callable[[Self], None]) -> Callable[[Self], None]:
        """
        Decorator for methods that modify cell values and/or candidates
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.update_candidates()

        return wrapper

    def paint_menu(self):
        self.puzzle_menu = PuzzleSelector(self.settings)
        self.menu_proxy = QGraphicsProxyWidget()
        self.menu_proxy.setWidget(self.puzzle_menu)
        self.addItem(self.menu_proxy)
        # TODO: chose this position based on sizes
        self.menu_proxy.setPos(-300, -50)
        self.puzzle_menu.data.connect(self.set_puzzle)

    def paint_message_box(self):
        self.puzzle_message_box = ErrorBox(self.settings)
        self.message_proxy = QGraphicsProxyWidget()
        self.message_proxy.setWidget(self.puzzle_message_box)
        self.addItem(self.message_proxy)
        # TODO: chose this position based on sizes
        self.message_proxy.setPos(-300, 150)

    def paint_buttons(self):
        def paint_button(widget, x, y):
            proxy = QGraphicsProxyWidget()
            proxy.setWidget(widget)
            proxy.setPos(x, y)
            self.addItem(proxy)

        x = count(35, 100)  # Set start x & x spacing
        y = repeat(-80)

        buttons = [
            {
                "x": next(x),
                "y": next(y),
                "widget": QPushButton("Auto Note"),
                "func": self.auto_note,
            },
            {
                "x": next(x),
                "y": next(y),
                "widget": QPushButton("Hint"),
                "func": self.show_hint,
            },
            {
                "x": next(x),
                "y": next(y),
                "widget": QPushButton("Solve"),
                "func": self.solve,
            },
            {
                "x": next(x),
                "y": next(y),
                "widget": QPushButton("Reset"),
                # self.reset would delete the button while signal is being executed
                # This would cause a seg fault. Timer lets signal finish before running
                # reset method on the next event loop cycle.
                "func": lambda: QTimer.singleShot(0, self.reset),
            },
        ]

        for button in buttons:
            paint_button(button["widget"], button["x"], button["y"])
            button["widget"].clicked.connect(button["func"])

        switch = QCheckBox("Toggle Mode")
        paint_button(switch, next(x), next(y))
        switch.stateChanged.connect(self.set_mode)
        self.cell_mode_widget = switch

    def __init__(
        self,
        # data: BoardData,
        settings: Settings,
    ):
        super().__init__()

        self.data = None
        self.settings = settings
        self.hint = None

        # self.paint_message_box()
        self.paint_menu()
        # TODO: hint should be tracked so it can be handled better
        # hint should be printed in paint_board instead. I think?
        # There should be a button somewhere that appears only when a hint is active
        # This button will apply the hint
        # The hint should be cleared when it is applied or when the user applies it themselves
        # Also needs proper highlighting
        # I can either keep a hintbox at all times and toggle its visibility based on if there is a hint
        # Or I can delete it when there isn't and make a new one.

        self.buttons_painted = False

        # True if cell mode False if candidates mode
        self.cell_mode = True

        self.board_painted = False

        self.techniques = None

    def set_mode(self):
        # self.cell_mode = not self.cell_mode
        self.cell_mode = not self.cell_mode_widget.isChecked()
        # TODO: display this somewhere

    def send_message(self, text: str, timeout: float):
        """
        Show a message in the error box
        """
        # TODO: HintBox should inherit from base class
        # This will probably just use that base or maybe different child
        # Just need a box to show some text that can disapear on click and maybe on timer

        # hint = HintBox(technique, self.settings)
        # hint.setPos(self.settings.sizes.cell * 9 + 5, 0)
        # self.hint = hint
        # self.addItem(hint)
        return

        print(text)
        self.puzzle_message_box.setText(text)
        # await asyncio.sleep(timeout)
        # time.sleep(timeout)
        # self.puzzle_message_box.clear()
        # TODO: steal some of the code I wrote to interact with imageboard APIs.
        # downloader_api.py rate limiter
        # that might be a good way to clear after certain time

    @_auto_note
    def set_puzzle(self, puzzle: Puzzle):
        print(puzzle.uuid)
        print(type(puzzle))
        self.puzzle = puzzle
        self.data = BoardData(puzzle)

        self.selected_cell = None
        # self.cells: list[list[Cell]] = []

        self.do_auto_note = self.settings.gameplay.auto_note

        if self.settings.gameplay.start_full:
            self.data.all_normal()

        solution = None
        for n, value in enumerate(self.data.solve()):
            if n > 1:
                raise ValueError("Board has multiple solutions")

            solution = value
        if solution is None:
            raise ValueError("Board has no solution")
        self.solution = solution

        self.removeItem(self.hint)
        del self.hint
        self.hint = None

        if self.board_painted:
            self.update_candidates()
            self.clear_highlight()
        else:
            self.paint_board()
            self.board_painted = True

    def paint_board(self):
        print("painting")
        # print("pb", text_hints(self.data.candidates))
        self.cells = []
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

        if not self.buttons_painted:
            self.paint_buttons()
            self.buttons_painted = True

        big_pen = QPen(self.settings.colours.big_border, self.settings.sizes.big_border)
        normal_pen = QPen(self.settings.colours.border, self.settings.sizes.border)
        width = self.settings.sizes.cell * 9

        # Draw cell borders
        for i in range(10):
            # Vertical
            x = i * self.settings.sizes.cell
            self.addLine(
                x,
                0,
                x,
                width,
                (big_pen if i % 3 == 0 else normal_pen),
            )

            # Horizontal
            y = i * self.settings.sizes.cell
            self.addLine(
                0,
                y,
                width,
                y,
                (big_pen if i % 3 == 0 else normal_pen),
            )

        # TODO: Avoid repainting stuff
        # This will increase every time a new puzzle is selected
        print(len(self.items()))

    def update_candidates(self):
        """
        Updates candidates and cells
        """
        # Techniques should be recalculated if candidates change
        self.techniques = None

        # Set value and candidates again for every cell
        for row, col in product(range(9), repeat=2):
            self.cells[row][col].set_candidates((self.data.candidates[:, row, col]))
            self.cells[row][col].set_value(self.data.cells[row, col])

    def cell_clicked(self, cell: Cell):
        self.clear_highlight(hint_highlight=False)

        self.selected_cell = cell
        if self.selected_cell:
            # Highlight to show cell selected
            self.selected_cell.highlight_background(self.settings.colours.selected)

            # Highlight to show adjacent cells
            for coord in npc.argwhere(
                npc.adjacent(np.array([self.selected_cell.row, self.selected_cell.col]))
            ):
                cell = self.cells[coord[0]][coord[1]]

                if cell != self.selected_cell:
                    cell.highlight_background(self.settings.colours.adjacent)

    def highlight_cells(self, args: tuple[Coords, str | QColor], *, lock=False):
        """
        Args:
            args:
                (coords of cells to highlight, colour to set cells to)
            lock: if True will not allow cell to be highlighted
                again until lock is removed.
        """
        cells = args[0]
        colour = args[1]
        coords = npc.normalise_coords(cells)
        for coord in coords:
            row, col = coord
            print("foo")
            self.cells[row][col].highlight_background(colour)
            if lock:
                self.cells[row][col].highlight_lock()

    def clear_highlight(self, hint_highlight=True, adjacent_highlight=True):
        # FIXME: clears adjacent when doing hint stuff
        print(hint_highlight, adjacent_highlight)
        for row in self.cells:
            for cell in row:
                if hint_highlight:
                    cell.highlight_unlock()
                elif not adjacent_highlight:
                    continue
                cell.highlight_background(None)

    def show_hint(self):
        def get_techniques():
            for technique in TECHNIQUES:
                # print(technique)
                x = technique(
                    self.data.candidates,
                    self.data.clues,
                    self.data.guesses,
                )
                yield from x.find()

        valid = True
        if self.techniques is not None:
            try:
                technique = next(self.techniques)
            except StopIteration:
                technique = None

                # If there isn't a technique it is worth trying get_techniques again
                # In case all techniques have been seen this can wrap around to start
                valid = False
        else:
            valid = False

        if not valid:
            self.techniques = get_techniques()
            try:
                technique = next(self.techniques)
            except StopIteration:
                # Will go to fallback technique
                technique = None

        print(technique)

        self.clear_highlight(adjacent_highlight=False)

        # Fallback hint
        # Give solution to random cell
        if technique is None:
            name = "Fallback Hint"
            try:
                # Pick random coordinate without cell
                coord = choice(np.argwhere(self.data.cells == -1))

            # All cells have a value
            except IndexError:
                try:
                    coord = choice(np.argwhere(self.data.cells != self.data.solution))
                except IndexError:
                    # All cells have correct value
                    # Board is solved
                    return

                name = "Incorrect Cell"

            new_cells = np.full((9, 9), -1, dtype=np.int8)
            num = self.data.solution[*coord]
            new_cells[*coord] = num

            print(coord)
            technique = Technique(
                name,
                [MessageCoords(coord, highlight=1), MessageText("is"), MessageNum(num)],
                Action(add_cells=new_cells),
            )

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
        print("poo")

        highlight_hint_cells = partial(self.highlight_cells, lock=True)
        self.hint.highlight_cells.connect(highlight_hint_cells)
        self.hint.send_highlights()
        self.addItem(hint)
        print("pao")

    @_update_candidates
    @_auto_note
    def remove_cell(self):
        """
        Remove the value for the currently selected cell.
        Will only work for guesses.
        """
        # Do not let user remove clues
        if self.selected_cell.clue:
            return

        self.data.remove_cell(self.selected_cell.row, self.selected_cell.col)

        # Restore all notes for the cell if auto_note is enabled
        if self.do_auto_note:
            new: Candidates = np.full((9, 9, 9), False, dtype=np.bool)
            new[:, self.selected_cell.row, self.selected_cell.col] = True
            self.data.add_candidates(new)

    @_auto_note
    def add_cell(self, value: int):
        """
        Sets the value at the currently selected cell
        Args:
            value: value to set the cell. Between 0 and 8 inclusive.
        """
        # if self.solution[self.selected_cell.row, self.selected_cell.col] != value:
        #     # TODO: dialog to show this
        #     print("Incorrect")
        #     return

        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[
            self.selected_cell.row,
            self.selected_cell.col,
        ] = value

        try:
            self.data.add_cells(new_cells)
        except InvalidBoard:
            # TODO: some kind of dialog message to show this
            self.send_message(
                "Cannot add cell as it would make puzzle unsolvable.", 10.0
            )
            return

        self.selected_cell.set_value(value)

    @_update_candidates
    def toggle_candidate(self, value: int):
        """
        Toggles whether value is a candidate at focused cell
        Args:
            value: value to set the cell. Between 0 and 8 inclusive.
        """
        delta_candidates: Candidates = np.full((9, 9, 9), False, dtype=np.bool)
        delta_candidates[
            value,
            self.selected_cell.row,
            self.selected_cell.col,
        ] = True

        # Remove
        if self.cells[self.selected_cell.row][self.selected_cell.col].candidates[value]:
            try:
                self.data.remove_candidates(delta_candidates)
            except InvalidBoard:
                # TODO: some kind of dialog message to show this
                self.send_message(
                    "Cannot add cell as it would make puzzle unsolvable.", 10.0
                )
                return
        # Add
        else:
            self.data.add_candidates(delta_candidates)

    @_update_candidates
    def auto_note(self):
        """
        Remove candidates if they are adjacent to a cell with their value.
        """
        self.data.auto_normal()
        print("aosdfi")
        print(self.data.candidates)

    @_update_candidates
    def apply_action(self, action: Action):
        """
        Apply the current hint to the board
        """
        print("aply")
        # TODO: somewhere I need to check if the action is actually valid
        # This should always be the case but a failsafe is worth adding
        try:
            self.data.apply_action(action)
        except InvalidBoard:
            # Very bad
            # Means technique is broken
            logging.error("Illegal action generated")
            return

        self.removeItem(self.hint)
        del self.hint
        self.hint = None

        self.clear_highlight(adjacent_highlight=False)
        if self.do_auto_note:
            self.auto_note()

    @_auto_note
    def apply_hint(self):
        if self.hint is None:
            return

        self.apply_action(self.hint.technique.action)

    @_update_candidates
    def solve(self):
        """
        Solve the puzzle automatically
        """
        self.removeItem(self.hint)
        del self.hint
        self.hint = None

        self.clear_highlight()

        self.data.auto_solve()

    def reload(self):
        self.set_puzzle(self.puzzle)

    def reset(self):
        """
        Resets the puzzle to its initial state
        """
        print("a")
        self.puzzle.reset()
        print("b")
        self.reload()
        print("c")

    def keyPressEvent(self, event) -> None:
        if self.data is None:
            return

        if not self.selected_cell:
            return

        key = Qt.Key(event.key())
        mods = event.modifiers()
        seq = QKeySequence(QKeyCombination(mods, key))
        binds = self.settings.keybinds

        number_keys = [i for s in binds.numbers.values() for i in s]
        if seq in number_keys:
            # self.clear_highlight()

            # TODO: maybe move somewhere else
            # Like as a decorator to add_cell and toggle_candidate
            if self.hint is not None:
                self.removeItem(self.hint)
                del self.hint
                self.hint = None

                self.clear_highlight(adjacent_highlight=False)

            value = None
            for k, v in binds.numbers.items():
                if key in v:
                    value = k - 1
                    break

            assert value is not None
            if self.cell_mode:
                self.add_cell(value)
            else:
                self.toggle_candidate(value)

        elif seq in binds.remove:
            # FIXME: doesn't persist after auto normal
            self.remove_cell()
        elif seq in binds.auto_note:
            self.auto_note()
        elif seq in binds.solve:
            self.solve()
        elif seq in binds.hint:
            self.show_hint()
        elif seq in binds.apply_hint:
            self.apply_hint()
        elif seq in binds.reset:
            self.reset()
        elif seq in binds.toggle_mode:
            self.cell_mode_widget.toggle()

        # Python's negative indexing will handle wrap around for L and U
        elif seq in binds.left:
            self.cell_clicked(
                self.cells[self.selected_cell.row][self.selected_cell.col - 1]
            )
        elif seq in binds.up:
            self.cell_clicked(
                self.cells[self.selected_cell.row - 1][self.selected_cell.col]
            )

        elif seq in binds.right:
            self.cell_clicked(
                self.cells[self.selected_cell.row][(self.selected_cell.col + 1) % 9]
            )
        elif seq in binds.down:
            self.cell_clicked(
                self.cells[(self.selected_cell.row + 1) % 9][self.selected_cell.col]
            )
        # If it isn't a recognised keybind do nothing


def main():
    app = QApplication()

    scene = Board(settings)
    view = QGraphicsView(scene)
    view.setFocusPolicy(Qt.StrongFocus)

    view.show()
    sys.exit(app.exec())


# TODO: sudoku board needs buttons as alternatives to all key binds
# Also needs a button to go to main menu
# Main menu should have a way to select puzzle
# Hint box should also go away if user does it themselves
