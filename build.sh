#!/bin/sh

python -m venv venv
. ./venv/bin/activate

./venv/bin/python3.13 -m pip install Nuitka==2.7.11 numpy==2.3.1 PySide6==6.10.0 patchelf==0.17.2.4

# TODO: replace icon with custom one
./venv/bin/python3.13 -m nuitka ./main.py --follow-imports --enable-plugin=pyside6 --output-dir=./bin --quiet --noinclude-qt-translations --onefile --noinclude-dlls=*.cpp.o --noinclude-dlls=*.qsb --linux-icon=/usr/lib/python3.13/site-packages/PySide6/scripts/deploy_lib/pyside_icon.jpg


