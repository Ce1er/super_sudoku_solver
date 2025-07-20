# Copyright 2025 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DESCRIPTION="Application to help solve sudoku puzzles"
HOMEPAGE="https://github.com/Ce1er/super_sudoku_solver"
SRC_URI=""

LICENSE="BSD-4"
SLOT="0"
KEYWORDS="~amd64"

DEPEND="
	dev-lang/python
	dev-python/numpy
	test? dev-python/pytest
"
RDEPEND="${DEPEND}"
BDEPEND=""
