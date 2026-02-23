from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
# TODO:: I feel like this would be better as .toml

# Each highlight group's corresponding rgba colour. These are for hints.
highlight_colours: dict[int, QColor] = {1: QColor(248, 252, 3, 255)}

number_colour: QColor = QColor(0, 0, 0, 255)
candidate_colour = QColor(30, 50, 78, 255)
special_candidate_colour = QColor(25, 1, 98, 255)
rejected_candidate_colour = QColor(255, 0, 0, 255)

border_colour: QColor = QColor(0, 0, 0, 255)
big_border_colour: QColor = QColor(0, 0, 0, 255)
background_colour: QColor = QColor(255, 255, 255, 255)
text_colour: QColor = QColor(0, 0, 0, 255)


border_size: int = 1
big_border_size: int = 3
cell_size: int = 60


remove_cell: list[Qt.Key] = [Qt.Key_Backspace]
add_cell: dict[int, list[Qt.Key]] = {
    1: [Qt.Key_1],
    2: [Qt.Key_2],
    3: [Qt.Key_3],
    4: [Qt.Key_4],
    5: [Qt.Key_5],
    6: [Qt.Key_6],
    7: [Qt.Key_7],
    8: [Qt.Key_8],
    9: [Qt.Key_9],
}
auto_note: list[Qt.Key] = [Qt.Key_N]
select_left: list[Qt.Key]
select_right: list[Qt.Key]
select_up: list[Qt.Key]
select_down: list[Qt.Key]
