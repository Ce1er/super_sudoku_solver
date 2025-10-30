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
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QColor
from PySide6.QtCore import QRectF, Qt
import sys
import numpy as np
import numpy.typing as npt
from typing import Optional
from itertools import product

import settings
from sudoku import Board as BoardData
from utils import get_first
from human_solver import HumanSolver, Technique


# TODO: pass in font so it is customisable
class Cell(QGraphicsItem):
    def __init__(
        self,
        coord: npt.NDArray[np.int8],
        candidates: npt.NDArray[np.bool],
        highlight_colours: dict[int, QColor],
        border_colour: QColor,
        background_colour: QColor,
        border_size: int,
        size: int,
        clue: bool,
    ) -> None:
        """
        Args:
            coord: [row, column, value] (all 0-8 inclusive but value can also be -1 to indicate no value)
            candidates: 1d boolean array where candidates[n] == True means number n+1 can be in cell
        """
        super().__init__()
        self.row: int = coord[0]
        self.col: int = coord[1]
        self.value: int = coord[2]
        self.candidates: npt.NDArray[np.bool] = candidates
        self.highlight: Optional[int] = None
        self.size: int = size
        self.clue: bool = clue

        self.border_colour = border_colour
        self.background_colour = background_colour
        self.highlight_colours = highlight_colours

        self.border_size = border_size

        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.highlighted = False

    def boundingRect(self):
        return QRectF(0, 0, self.size, self.size)

    def paint(self, painter, option, widget):
        if self.highlight:
            painter.fillRect(
                self.boundingRect(),
                QBrush(self.highlight_colours.get(self.highlight)),
            )
        else:
            painter.fillRect(self.boundingRect(), QBrush(self.background_colour))

        pen = QPen(self.border_colour, self.border_size)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        if self.value != -1:
            if self.clue:
                painter.setFont(QFont("Arial", int(self.size * 0.5), QFont.Bold))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.value))
            else:
                painter.setFont(QFont("Arial", int(self.size * 0.5)))
                painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self.value))

        elif np.count_nonzero(self.candidates) != 0:
            painter.setFont(QFont("Arial", int(self.size * 0.2)))
            width = self.size / 3
            height = self.size / 3
            for i in range(9):
                if self.candidates[i]:
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
        self.value = value
        if value != -1:
            self.candidates = np.full([9], False)
        self.update()

    def set_candidates(self, value: npt.NDArray[np.bool]):
        self.candidates = value
        self.update()

    def set_highlighted(self, value: bool):
        self.highlighted = value
        self.update()


# NOTE: Use QLabel instead? Doing things manually does increase flexibility but maybe QLabel is enough.
class HintBox(QGraphicsItem):
    def __init__(
        self,
        technique: Technique,
        text_size,
        border_colour,
        border_size,
        background_colour,
        height
    ):  # TODO: take colours and stuff as well. Probably should implement Action before trying to get cell highlighting working but the message box part can be done at any time.
        super().__init__()

        # TODO: Width and height set based on text length.
        self.width = len(technique.get_message()) * text_size
        self.height = height

        self.technique = technique
        self.text_size = text_size
        self.border_colour = border_colour
        self.border_size = border_size
        self.background_colour = background_colour

        pass

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(self.background_colour))
        pen = QPen(self.border_colour, self.border_size)
        painter.setPen(pen)
        painter.drawRect(self.boundingRect())

        painter.setFont(QFont("Arial", self.text_size))
        # TODO: handle special text highlighting and stuff.
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.technique.message)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent, /) -> None:
        # TODO: handle mouse press event to do smth.
        return super().mousePressEvent(event)



class Board(QGraphicsScene):
    def __init__(
        self,
        data: BoardData,
        highlight_colours: dict[int, QColor],
        border_colour: QColor,
        background_colour: QColor,
        border_size: int,
        big_border_colour: QColor,
        big_border_size: int,
        cell_size: int = 60,
    ):
        super().__init__()
        self.data = data
        self.cell_size = cell_size

        self.selected_cell = None
        self.cells: list[list[Cell]] = []

        self.highlight_colours = highlight_colours
        self.border_colour = border_colour
        self.background_colour = background_colour
        self.border_size = border_size
        self.big_border_colour = big_border_colour
        self.big_border_size = big_border_size
        self.paint_board()

    def paint_board(self):
        x = -1
        for row, col in product(range(9), repeat=2):
            if row > x:
                x = row
                self.cells.append([])
            for coord in self.data.get_cells():
                if coord[0] == row and coord[1] == col:
                    value = coord[2]
                    break
            else:
                value = -1

            print("foo", self.data.is_clue(np.array([row, col])))
            cell = Cell(
                np.array([row, col, value]),
                self.data.get_candidates()[row, col],
                self.highlight_colours,
                self.border_colour,
                self.background_colour,
                self.border_size,
                self.cell_size,
                self.data.is_clue(np.array([row, col])),
            )
            cell.setPos(col * self.cell_size, row * self.cell_size)
            self.addItem(cell)
            self.cells[-1].append(cell)

        pen = QPen(self.big_border_colour, self.big_border_size)
        for i in range(10):
            width = self.cell_size * 9
            x = i * self.cell_size
            self.addLine(
                x,
                0,
                x,
                width,
                pen if i % 3 == 0 else QPen(self.border_colour, self.border_size),
            )

            y = i * self.cell_size
            self.addLine(
                0,
                y,
                width,
                y,
                pen if i % 3 == 0 else QPen(self.border_colour, self.border_size),
            )

    def update_candidates(self):
        """
        Updates candidates and cells
        """
        for row, col in product(range(9), repeat=2):
            self.cells[row][col].set_candidates(
                (self.data.get_candidates()[:, row, col])
            )
            self.cells[row][col].set_value(self.data.get_all_cells()[row, col])

    def cell_clicked(self, cell: Cell):
        if self.selected_cell:
            self.selected_cell.set_highlighted(False)
        self.selected_cell = cell
        cell.set_highlighted(True)

    def show_hint(self):
        human = HumanSolver(self.data)
        print(type(human))

        # NOTE: finding a hint relies on candidates being set. It does not auto_normal automatically.
        technique = get_first(human.hint())
        if technique is None:
            print("No technique found")
            return

        hint = HintBox(
            technique, 11, self.border_colour, self.border_size, self.background_colour, self.cell_size
        )
        hint.setPos(self.cell_size * 9+5, 0)
        self.addItem(hint)

        print(technique.message)

    def keyPressEvent(self, event) -> None:
        # TEMPORARY HARDCODED KEYBINDS
        # LMB - select cell
        # 1-9 enter cell
        # a - autonote
        if not self.selected_cell:
            return

        key = event.key()
        if Qt.Key_1 <= key <= Qt.Key_9:
            value = key - Qt.Key_0 - 1
            self.selected_cell.set_value(value + 1)
            self.data.add_cell(
                np.array(
                    [
                        self.selected_cell.row,
                        self.selected_cell.col,
                        self.selected_cell.value,
                    ]
                )
            )
        # TODO: keybindings in settings.py
        elif key == Qt.Key_Backspace:
            self.selected_cell.set_value(-1)
        elif key == Qt.Key_A:
            # FIXME: doesn't do anything when used after the user inputs a guess
            self.data.auto_normal()
            self.update_candidates()
        elif key == Qt.Key_S:
            self.data.auto_solve()
            self.update_candidates()
        elif key == Qt.Key_H:
            self.show_hint()


def main():
    app = QApplication(sys.argv)
    scene = Board(
        BoardData(
            # "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
            # "................................................................................."
                    ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."

        ),
        settings.highlight_colours,
        settings.border_colour,
        settings.background_colour,
        settings.border_size,
        settings.big_border_colour,
        settings.big_border_size,
        settings.cell_size,
    )
    view = QGraphicsView(scene)
    view.setFocusPolicy(Qt.StrongFocus)
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
