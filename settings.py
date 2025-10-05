from PySide6.QtGui import QColor

# Each highlight group's corresponding rgba colour
highlight_colours: dict[int, QColor] = {1: QColor(248, 252, 3, 255)}
border_colour: QColor = QColor(0, 0, 0, 255)
big_border_colour: QColor = QColor(0, 0, 0, 255)
background_colour: QColor = QColor(255, 255, 255, 255)


border_size: int = 1
big_border_size: int = 3
cell_size: int = 60
