from typing import Callable, Optional, Self, Any, SupportsInt, assert_never, override

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsProxyWidget,
    QGraphicsTextItem,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QCheckBox,
    QStyle,
    QVBoxLayout,
)
from PySide6.QtGui import (
    QKeySequence,
    QPen,
    QBrush,
    QFont,
    QColor,
    QTextDocument,
    QPainter,
)
from PySide6.QtCore import QKeyCombination, QRectF, Qt, Signal, QTimer, QObject

import sys
import logging

from functools import wraps, partial
from itertools import product, count, repeat
from random import choice
from html import escape

import super_sudoku_solver.np_candidates as npc
import numpy as np
import numpy.typing as npt

from super_sudoku_solver.sudoku import Board
from super_sudoku_solver.sudoku import InvalidBoard
from super_sudoku_solver.save_manager import Puzzles

from super_sudoku_solver.techniques import TECHNIQUES
import super_sudoku_solver.human_solver as human_solver

from super_sudoku_solver.settings import settings, Settings

from super_sudoku_solver.human_solver import (
    MessageCoords,
    MessageText,
    MessageNums,
    Technique,
    Action,
)
from super_sudoku_solver.custom_types import Candidates, CellCandidates, Cells, Coords
from super_sudoku_solver.custom_types import Cell as CellT


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

        self._row: int = coord[0]
        self._col: int = coord[1]

        self._value: int = -1 if coord[2] == -1 else coord[2] + 1
        self._candidates: npt.NDArray[np.bool] = candidates
        self._is_clue: bool = clue

        self._size: int = settings.sizes.cell
        self._border_size = settings.sizes.border

        self._border_colour = settings.colours.border
        self._background_colour = settings.colours.board_background

        self._candidate_pen = QPen(settings.colours.candidate)
        self._clue_pen = QPen(settings.colours.clue)
        self._guess_pen = QPen(settings.colours.guess)

        self._is_highlighted = False
        self._highlight_locked = False

        self.setAcceptedMouseButtons(Qt.LeftButton)

    @property
    def highlight_locked(self):
        """
        Is the cell's highlight locked?
        Note:
            highlight_lock() and highlight_unlock() should be used to set value
        """
        return self._highlight_locked

    @property
    def is_highlighted(self):
        """Is this cell currently highlighted?"""
        return self._is_highlighted

    @property
    def is_clue(self):
        """Is this cell a clue?"""
        return self._is_clue

    @is_clue.setter
    def is_clue(self, value: bool):
        self._is_clue = value

    @property
    def row(self):
        """0-based index of Cell's row"""
        return self._row

    @property
    def col(self):
        """0-based index of Cell's column"""
        return self._col

    @property
    def value(self):
        """0-Based value of Cell. -1 if no value."""
        return self._value

    # GUI update is expensive so property setter feels wrong here
    def set_value(self, value: int):
        if not -1 <= value <= 8:
            raise ValueError(f"Cannot set cell value to {value}, not in range [0,8]")

        self._value = -1 if value == -1 else value + 1
        if value != -1:
            self._candidates = np.full([9], False)
        self.update()

    @property
    def candidates(self):
        return self._candidates

    def set_candidates(self, value: CellCandidates):
        if value.shape != (9,):
            raise ValueError(f"Invalid candidates shape {value.shape}")
        if value.dtype != np.bool:
            raise TypeError(f"Invalid candidates dtype {value.dtype}")

        self._candidates = value
        self.update()

    def highlight_lock(self):
        """Don't allow highlight to change until unlocked"""
        self._highlight_locked = True

    def highlight_unlock(self):
        """Allow highlight to be changed"""
        self._highlight_locked = False

    def highlight_background(self, colour: None | Any):
        """
        Change background colour for the cell. Unless highlight lock is enabled.
        Args:
            colour: None to reset to default. Anything QColor can interpret to set new colour.
        """
        if self._highlight_locked:
            return

        if colour is None:
            self._is_highlighted = False
            new = self.settings.colours.board_background
        else:
            self._is_highlighted = True
            new = QColor(colour)

        # QColor doesn't raise an error for all invalid inputs
        if not new.isValid():
            raise ValueError("Could not interpret colour for cell background")

        self._background_colour = new
        self.update()

    @override
    def boundingRect(self):
        return QRectF(0, 0, self._size, self._size)

    @override
    def paint(self, painter, option, widget):
        # Draw background
        painter.fillRect(self.boundingRect(), QBrush(self._background_colour))

        # Draw border
        pen = QPen(self._border_colour, self._border_size)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        # Draw value
        if self._value != -1:
            if self.is_clue:
                painter.setPen(self._clue_pen)
                painter.setFont(QFont("Arial", int(self._size * 0.5), QFont.Bold))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self._value))
            else:
                painter.setPen(self._guess_pen)
                painter.setFont(QFont("Arial", int(self._size * 0.5)))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self._value))

        # Draw candidates
        elif np.count_nonzero(self._candidates) != 0:
            painter.setFont(QFont("Arial", int(self._size * 0.2)))
            painter.setPen(self._candidate_pen)
            width = self._size / 3
            height = self._size / 3
            for i in range(9):
                if self._candidates[i]:
                    row = i // 3
                    column = i % 3
                    x = column * width
                    y = row * height
                    painter.drawText(
                        QRectF(x, y, width, height), Qt.AlignCenter, str(i + 1)
                    )

    @override
    def mousePressEvent(self, event) -> None:
        scene = self.scene()
        if hasattr(scene, "cell_clicked"):
            scene.cell_clicked(self)
        else:
            raise RuntimeError("Scene does not have method cell_clicked")
        event.accept()


# This class is mostly a QGraphicsItem but QObject is needed for Signal.
# So inherit both.
class HintBox(QGraphicsItem, QObject):
    """
    Signals:
        highlight_cells:
            Sends the cells to highlight based on technique
            Emits: tuple[Coords, QColor]
    """

    highlight_cells = Signal(tuple)

    def __init__(
        self,
        technique: Technique,
        settings: Settings,
    ):

        QObject.__init__(self)
        QGraphicsItem.__init__(self)

        self.settings = settings

        self.technique = technique

        self.highlight_cells_calls: list[tuple[Coords, QColor]] = []

        # TODO: move to settings
        # colours: dict[int, QColor] = {
        #     1: QColor("#dc8a78"),
        #     2: QColor("#8839ef"),
        #     3: QColor("#d20f39"),
        # }
        colours = self.settings.colours.hint_highlight

        # Title / technique name
        html = f'<span style="color: {self.settings.colours.text.name()};"'
        html += "<b>" + escape(self.technique.technique) + "</b><br>"

        # Technique description with optional highlighting
        for message_part in self.technique.message_parts:
            if message_part.highlight is not None:
                html += f'<span style="background-color: {colours[message_part.highlight].name()}"><b>{escape(message_part.text)}</b></span>'

                # Save data about cells which should be highlighted
                if isinstance(message_part, human_solver.MessageCoords):
                    self.highlight_cells_calls.append(
                        (message_part.coords, colours[message_part.highlight])
                    )
            else:
                if isinstance(message_part, MessageNums):
                    html += "<b>" + escape(message_part.text) + "</b>"
                else:
                    html += escape(message_part.text)

            html += " "

        html += r"<br><b>Click to apply<\b>"
        html += r"<\span>"

        # FIXME: hardcoded
        self._width = 200
        self._text = QTextDocument()
        self._text.setHtml(html)
        self._text.setTextWidth(self._width)
        self.settings = settings
        self._height = self._text.size().height()

        self._text_size = settings.sizes.text

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def text(self):
        return self._text

    def send_highlights(self):
        for call in self.highlight_cells_calls:
            self.highlight_cells.emit(call)

    @override
    def boundingRect(self):
        return QRectF(0, 0, self._width, self._height)

    @override
    def paint(self, painter: QPainter, option, widget):
        # Draw background
        painter.fillRect(self.boundingRect(), QBrush(settings.colours.hint_background))

        # Draw border
        pen = QPen(self.settings.colours.border, self.settings.sizes.border)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        # Draw text
        painter.setFont(QFont("Arial", self._text_size))
        painter.save()
        self._text.drawContents(painter)
        painter.restore()

    @override
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent, /) -> None:
        """
        On LMB apply action
        """
        # TODO: somehow this action needs to be passed back up to Board
        # and it should handle it by applying the action
        scene = self.scene()
        if hasattr(scene, "apply_action"):
            scene.apply_action(self.technique.action)
        else:
            raise RuntimeError("Scene does not have method apply_action")
        event.accept()


class PuzzleSelector(QListWidget):
    """
    Signals:
        data: the Board of the puzzle selected
    """

    data = Signal(Board)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

        self._puzzles = Puzzles().puzzle_map
        puzzle_names = list(self._puzzles.keys())
        self.addItems(puzzle_names)

        self.itemClicked.connect(self.puzzle_selected)

    def puzzle_selected(self, item):
        self.data.emit((self._puzzles[item.text()]))
        # TODO: use signals in the other classes


class MainScene(QGraphicsScene):
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
        self.puzzle_menu.setStyleSheet(f"""
                                       QListWidget {{ 
                                         color: {self.settings.colours.text.name()}; 
                                         background-color: {self.settings.colours.menu_background.name()};
                                       }}
                                       """)

        self.menu_proxy = QGraphicsProxyWidget()
        self.menu_proxy.setWidget(self.puzzle_menu)
        self.addItem(self.menu_proxy)

        width = self.menu_proxy.geometry().width()
        padding = self.settings.sizes.cell
        self.menu_proxy.setPos(-(width + padding), 0)

        self.puzzle_menu.data.connect(self.set_puzzle)

    def paint_message_box(self):
        self.message_box = QGraphicsTextItem()
        self.message_box.setPos(-300, -100)
        self.message_box.hide()
        self.addItem(self.message_box)
        # self.puzzle_message_box = ErrorBox(self.settings)
        # self.message_proxy = QGraphicsProxyWidget()
        # self.message_proxy.setWidget(self.puzzle_message_box)
        # self.addItem(self.message_proxy)
        # # TODO: chose this position based on sizes
        # self.message_proxy.setPos(-300, 150)

    def paint_buttons(self):
        # def paint_button(widget):
        #     proxy = QGraphicsProxyWidget()
        #     proxy.setWidget(widget)
        #     self.addItem(proxy)

        def wrap(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                except RuntimeWarning as e:
                    self.send_message(str(e))
                    return

                return result

            return wrapped

        def item(text, item_type):
            x = item_type(text)
            x.setStyleSheet(f"""
                            color: {self.settings.colours.text.name()}; 
                            background-color: {self.settings.colours.button_background.name()};
                            """)
            proxy = QGraphicsProxyWidget()
            proxy.setWidget(x)
            self.addItem(proxy)
            return proxy

        button = partial(item, item_type=QPushButton)
        switch = partial(item, item_type=QCheckBox)

        buttons = [
            # {
            #     "widget": button("Auto Note"),
            #     "func": wrap(self.auto_note),
            # },
            {
                "type": "button",
                "widget": button("Hint"),
                "func": wrap(self.show_hint),
            },
            {
                "type": "button",
                "widget": button("Solve"),
                "func": wrap(self.solve),
            },
            {
                "type": "button",
                "widget": button("Reset"),
                "func": wrap(self.reset),
            },
            {
                "type": "switch",
                "widget": switch("Candidates Mode"),
                "func": wrap(self.reset),
            },
        ]

        total_width = sum(button["widget"].rect().width() for button in buttons)
        left = self.cells[0][0].x()
        right = self.cells[-1][-1].x() + self.settings.sizes.cell

        total_padding = (right - left) - total_width
        if total_padding < 0:
            raise ValueError("Buttons cannot be painted as board is not wide enough.")

        padding = total_padding / (len(buttons) - 1)

        x = left
        y = -self.settings.sizes.cell * 0.8

        for button in buttons:
            if button["type"] == "button":
                button["widget"].widget().clicked.connect(button["func"])
            elif button["type"] == "switch":
                button["widget"].widget().stateChanged.connect(self.set_mode)
                self.cell_mode_widget = button["widget"].widget()
            else:
                assert_never(button["widget"])

            print(x, button["widget"].rect().width())
            button["widget"].setPos(x, y)
            x += button["widget"].rect().width() + padding

        self.buttons_painted = True

    def __init__(
        self,
        # data: BoardData,
        settings: Settings,
    ):
        super().__init__()

        self.data = None
        self.settings = settings
        self.hint = None

        self.paint_message_box()
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

        self.message_time = 2500

    def set_mode(self):
        # self.cell_mode = not self.cell_mode
        self.cell_mode = not self.cell_mode_widget.isChecked()
        # TODO: display this somewhere

    def send_message(self, text: str, timeout: Optional[int] = None):
        """
        Show a message in the error box
        Args:
            text: text to show
            timeout: time to display (in ms)
        """
        if timeout is None:
            timeout = self.message_time
        self.message_box.setHtml(
            r"""
                                 <span style="
                                    background-color: {};
                                    color: {};
                                 ">
                                 {}
                                 <\span>
                                 """.format(
                self.settings.colours.message_background.name(),
                self.settings.colours.text.name(),
                escape(text),
            )
        )
        self.message_box.show()
        QTimer.singleShot(timeout, self.message_box.hide)

    @_auto_note
    def set_puzzle(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.data = Board(puzzle)

        self.selected_cell = None
        # self.cells: list[list[Cell]] = []

        self.do_auto_note = self.settings.gameplay.auto_note

        if self.settings.gameplay.start_full:
            self.data.all_normal()

        if self.hint is not None:
            self.removeItem(self.hint)
        self.hint = None

        if self.board_painted:
            self.update_candidates()
            self.clear_highlight()
        else:
            self.paint_board()

    def paint_board(self):
        """
        Paint board from (0, 0) to (self.settings.sizes.cell * 9, self.settings.sizes.cell * 9)
        """
        if self.data is None:
            raise RuntimeError("Could not paint board as there is no board data.")

        self.cells = []
        x = -1
        for row, col in product(range(9), repeat=2):
            if row > x:
                x = row
                self.cells.append([])
            value = self.data.cells[row, col]

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

        self.board_painted = True

    def update_candidates(self):
        """
        Updates candidates and cells
        Raises:
            RuntimeWarning: called without active board
        """
        if self.data is None:
            raise RuntimeWarning("Update candidates called without active board")

        # Techniques should be recalculated if candidates change
        self.techniques = None

        # Set value and candidates again for every cell
        for row, col in product(range(9), repeat=2):
            self.cells[row][col].set_candidates((self.data.candidates[:, row, col]))
            self.cells[row][col].set_value(self.data.cells[row, col])
            self.cells[row][col].is_clue = self.data.is_clue(np.array([row, col]))

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
            self.cells[row][col].highlight_background(colour)
            if lock:
                self.cells[row][col].highlight_lock()

    def clear_highlight(self, hint_highlight=True, adjacent_highlight=True):
        for row in self.cells:
            for cell in row:
                if cell.highlight_locked:
                    if hint_highlight:
                        cell.highlight_unlock()
                else:
                    if not adjacent_highlight:
                        continue
                cell.highlight_background(None)

    def show_hint(self):
        """
        Raises:
            RuntimeWarning: no reason to show hint
            RuntimeError: failed to generate hint
        """
        if self.data is None:
            raise RuntimeWarning("Show hint called without board active")
        if self.data.is_solved:
            raise RuntimeWarning("Board is solved, no reason to give hint")

        valid = False
        technique = None
        if self.techniques is not None:
            try:
                technique = next(self.techniques)
                valid = True
            except StopIteration:
                # This error just means the end of the self.techniques iterator
                # has been reached. There may still be valid techniques for board
                # as they may have all been iterated over.
                pass

        if not valid:
            self.techniques = self.data.hint()
            try:
                technique = next(self.techniques)
            except StopIteration:
                # There are no valid techniques for board
                pass

        # Fallback hint
        # Give solution to random cell
        if technique is None:
            try:
                coord = choice(
                    np.argwhere(
                        np.logical_and(
                            self.data.cells != self.data.solution, self.data.cells != -1
                        )
                    )
                )
                name = "Incorrect Cell"

            # There are no incorrect cells
            except IndexError:
                try:
                    # Pick random coordinate without cell
                    coord = choice(np.argwhere(self.data.cells == -1))
                    name = "Fallback Technique"
                except IndexError as e:
                    raise RuntimeError("Failed to generate fallback technique") from e

            new_cells = np.full((9, 9), -1, dtype=np.int8)
            num = self.data.solution[*coord]
            new_cells[*coord] = num

            technique = Technique(
                name,
                [
                    MessageCoords(coord, highlight=1),
                    MessageText("is"),
                    MessageNums(num),
                ],
                Action(add_cells=new_cells),
            )

        if self.hint is not None:
            self.removeItem(self.hint)

        hint = HintBox(technique, self.settings)
        hint.setPos(self.settings.sizes.cell * 9.3, 0)
        self.hint = hint

        # Clear any previous hint highlights
        self.clear_highlight(adjacent_highlight=False)

        # Highlight cells
        highlight_hint_cells = partial(self.highlight_cells, lock=True)
        self.hint.highlight_cells.connect(highlight_hint_cells)
        self.hint.send_highlights()
        self.addItem(hint)

    @_auto_note
    def add_cell(self, value: int):
        """
        Sets the value at the currently selected cell
        Args:
            value: value to set the cell. Between 0 and 8 inclusive.
        Raises:
            RuntimeWarning: cell could not be added, warn user
            InvalidBoard: cell could not be added, no warning needed
        """
        if self.data is None:
            raise InvalidBoard("Add cell called without board active")
        if self.selected_cell is None:
            raise InvalidBoard("Could not add cell as no cell is selected")
        if self.selected_cell.is_clue:
            raise InvalidBoard("Could not add cell as it would override a clue")
        if self.selected_cell.value != -1:
            raise RuntimeWarning("Could not add cell as it would override a guess")

        new_cells: Cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[
            self.selected_cell.row,
            self.selected_cell.col,
        ] = value

        try:
            self.data.add_cells(new_cells)
        except InvalidBoard as e:
            raise RuntimeWarning(
                "Cannot add cell as it would make puzzle unsolvable."
            ) from e

        self.selected_cell.set_value(value)

    @_update_candidates
    def toggle_candidate(self, value: int):
        """
        Toggles whether value is a candidate at focused cell
        Args:
            value: value to set the cell. Between 0 and 8 inclusive.
        Raises:
            RuntimeError: candidate could not be toggled
            RuntimeWarning: there is no board to toggle candidate for
            InvalidBoard: toggling candidate is a mistake and allow mistakes is disabled
        """
        if self.data is None:
            raise RuntimeWarning("Toggle candidate called without board active")
        if self.selected_cell is None:
            raise RuntimeError("Could not toggle candidate as no cell is selected")
        if self.selected_cell.value != -1:
            raise RuntimeError(
                "Could not toggle candidate for cell as it already has a value"
            )

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
            except InvalidBoard as e:
                raise RuntimeWarning(
                    "Cannot remove candidate as it would make puzzle unsolvable."
                ) from e
        # Add
        else:
            return
            self.data.add_candidates(delta_candidates)

    @_update_candidates
    def auto_note(self):
        """
        Remove candidates if they are adjacent to a cell with their value.
        Raises:
            RuntimeWarning: there is no board to auto note
        """
        if self.data is None:
            raise RuntimeWarning("Auto note called without board active")

        self.data.auto_normal()

    @_update_candidates
    def apply_action(self, action: Action, from_hint: bool = True):
        """
        Apply an Action to the board.
        Args:
            action: Action to apply
            from_hint: whether the Action came from a hint. If True will delete hint after application.
        Raises:
            RuntimeError: action could not be applied to board
            RuntimeWarning: there is no board to apply action to
        """
        if self.data is None:
            raise RuntimeWarning("Apply action called without board active")
        if from_hint and self.hint is None:
            raise RuntimeError(
                "Action to be applied claims to come from hint but self.hint is None"
            )

        try:
            self.data.apply_action(action)
        except InvalidBoard as e:
            raise RuntimeError("Illegal action generated") from e

        if from_hint:
            self.removeItem(self.hint)
            self.hint = None

        self.clear_highlight(adjacent_highlight=False)
        if self.do_auto_note:
            self.auto_note()

    @_auto_note
    def apply_hint(self):
        # Handles user using apply hint keybind without active hint.
        if self.hint is None:
            return

        self.apply_action(self.hint.technique.action)

    @_update_candidates
    def solve(self):
        """
        Solve the puzzle automatically
        """
        if self.hint is not None:
            self.removeItem(self.hint)
        self.hint = None

        self.clear_highlight()

        self.data.auto_solve()

    def reload(self):
        self.set_puzzle(self.puzzle)

    def reset(self):
        """
        Resets the puzzle to its initial state
        """
        self.puzzle.reset()
        self.reload()

    @override
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
        try:
            if seq in number_keys:
                if self.hint is not None:
                    self.removeItem(self.hint)
                    self.hint = None

                    self.clear_highlight(adjacent_highlight=False)

                value = None
                for k, v in binds.numbers.items():
                    if key in v:
                        value = k - 1
                        break

                assert value is not None
                try:
                    if self.cell_mode:
                        self.add_cell(value)
                    else:
                        self.toggle_candidate(value)

                except InvalidBoard:
                    # Action couldn't be performed for a reason that doesn't need a message
                    # e.g. there isn't a board selected
                    pass

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

        # User did an invalid action
        except RuntimeWarning as e:
            self.send_message(str(e))

        # Same as before
        except RuntimeError:
            pass


class View(QGraphicsView):
    """Responsible for window resizes and drawing background"""

    def __init__(self, scene, margin):
        super().__init__(scene)

        self.setViewportMargins(margin, margin, margin, margin)

    @override
    def resizeEvent(self, event):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)


def main():
    app = QApplication()

    scene = MainScene(settings)
    view = View(scene, settings.sizes.margin)
    view.setStyleSheet(
        f"QGraphicsView {{ background: {settings.colours.background.name()}; border: none; }}"
    )

    view.setFocusPolicy(Qt.StrongFocus)

    view.show()
    sys.exit(app.exec())
