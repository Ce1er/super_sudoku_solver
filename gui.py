from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QColor
from PySide6.QtCore import QRectF, Qt
import sys
import numpy as np
import numpy.typing as npt
from typing import Optional
from itertools import product

import settings
from sudoku import Board as BoardData


class Cell(QGraphicsItem):
    def __init__(
        self,
        coord: npt.NDArray[np.int8],
        candidates: npt.NDArray[np.bool],
        highlight_colours: dict[int, QColor],
        border_colour: QColor,
        background_colour: QColor,
        border_size: int = 1,
        size: int = 60,
    ) -> None:
        """
        Args:
            coord: [row, column, value] (all 0-8 inclusive but value can also be -1 to indicate no value)
            candidates: 1d boolean array where candidates[n] == True means number n+1 can be in cell
        """
        super().__init__()
        self.row: int = coord[0] + 1
        self.col: int = coord[1] + 1
        self.value: int = coord[2] + 1 if coord[2] != -1 else -1
        self.candidates: npt.NDArray[np.bool] = candidates
        self.highlight: Optional[int] = None
        self.size: int = size

        self.border_colour = border_colour
        self.background_colour = background_colour
        self.highlight_colours = highlight_colours

        self.border_size = border_size

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

        self.highlight_colours = highlight_colours
        self.border_colour = border_colour
        self.background_colour = background_colour
        self.border_size = border_size
        self.big_border_colour = big_border_colour
        self.big_border_size = big_border_size
        self.paint_board()

    def paint_board(self):
        for row, col in product(range(9), repeat=2):
            for coord in self.data.get_cells():
                if coord[0] == row and coord[1] == col:
                    value = coord[2]
                    break
            else:
                value = -1

            cell = Cell(
                np.array([row, col, value]),
                self.data.get_candidates()[row, col],
                self.highlight_colours,
                self.border_colour,
                self.background_colour,
                self.border_size,
                self.cell_size,
            )
            cell.setPos(col * self.cell_size, row * self.cell_size)
            self.addItem(cell)

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


def main():
    app = QApplication(sys.argv)
    scene = Board(
        BoardData(
            "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
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
    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
