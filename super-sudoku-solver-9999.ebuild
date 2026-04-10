EAPI=8

PYTHON_COMPAT=( python3_14 )

DISTUTILS_USE_PEP517=setuptools
inherit distutils-r1 desktop

DESCRIPTION="Application to help solve sudoku puzzles"
HOMEPAGE="https://github.com/Ce1er/super_sudoku_solver"

inherit git-r3
EGIT_REPO_URI="https://github.com/Ce1er/super_sudoku_solver.git"
KEYWORDS="~amd64"

LICENSE="BSD-4"
SLOT="0"
IUSE="test"
REQUIRED_USE="${PYTHON_REQUIRED_USE}"


RDEPEND="
	${PYTHON_DEPS}
	$(python_gen_cond_dep '
	dev-python/iniconfig[${PYTHON_USEDEP}]
	>=dev-python/numpy-2.4.4[${PYTHON_USEDEP}]
	dev-python/jsonschema[${PYTHON_USEDEP}]
	>=dev-python/pyside-6[${PYTHON_USEDEP}]
	dev-python/appdirs[${PYTHON_USEDEP}]
	')
"
BDEPEND="
	${RDEPEND}
	$(python_gen_cond_dep '
	test? (
		>=dev-python/pytest-8.4.1[${PYTHON_USEDEP}]
		)
	')
"

distutils_enable_tests pytest


src_install() {
	distutils-r1_src_install

	domenu "${S}/super-sudoku-solver.desktop"

	elog "Default puzzles can be generated with the following command:"
	elog "$ super-sudoku-solver --restore-default-puzzles"
	elog ""
	elog "A skeleton configuration file can be written using the following command"
	elog "$ super-sudoku-solver --restore-default-config"
}
