from sudoku import Board as BoardData

# TODO: PyQt6 and PySide6 do the same thing but are not compatible. Choose which one to use.
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLineEdit,
    QLabel,
    QGridLayout,
    QListWidget,
)
from PyQt6.QtCore import Qt
from PySide6.QtGui import QPainter, QPaintDevice
from PySide6.QtCore import QRect

from itertools import product
from collections import defaultdict


class Cell(QPaintDevice):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidates = []
        self.initial_value = None
        self.entered_value = None

    def set_candidates(self, candidates):
        self.candidates = candidates

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self.initial_value:
            font = painter.font()
            font.setPointSize(24)
            painter.setFont(font)
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, str(self.initial_value)
            )
        elif self.entered_value:  # TODO: make look different from initial value
            font = painter.font()
            font.setPointSize(24)
            painter.setFont(font)
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, str(self.entered_value)
            )
        else:
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            for candidate in self.candidates:
                row, col = divmod(candidate - 1, 3)
                sub_rect = QRect(
                    rect.left() + col * self.width() // 3,
                    rect.top() + row * self.height() // 3,
                    self.width() // 3,
                    self.height() // 3,
                )
                painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, str(candidate))


class Board(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        layout = QGridLayout()
        self.setLayout(layout)
        self.board = BoardData("." * 81)
        self.cells = defaultdict()

        for row, column in product(range(9), repeat=2):
            cell = Cell()
            self.cells[(row, column)] = cell
            layout.addWidget(cell, row, column)

    def foo(self): ...


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Sudoku")

        layout = QGridLayout()
        self.setLayout(layout)

        layout.addWidget(Board())

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
