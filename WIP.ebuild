EAPI=8

PYTHON_COMPAT=( python3_14 )

inherit python-r1 desktop

DESCRIPTION="Application to help solve sudoku puzzles"
HOMEPAGE="https://github.com/Ce1er/super_sudoku_solver"

inherit git-r3
EGIT_REPO_URI="https://github.com/Ce1er/super_sudoku_solver.git"

LICENSE="BSD-4"
SLOT="0"
REQUIRED_USE="${PYTHON_REQUIRED_USE}"

ISE="test"

RDEPEND="
	${PYTHON_DEPS}
	$(python_gen_cond_dep '
	>=dev-python/iniconfig[${PYTHON_USEDEP}]-2.1.0
	>=dev-python/numpy[${PYTHON_USEDEP}]-2.4.2
	>=dev-python/pygments[${PYTHON_USEDEP}]-2.26.0
	>=dev-python/jsonschema[${PYTHON_USEDEP}]-8.4.1
	>=dev-python/pyside[${PYTHON_USEDEP}]-6.10.2
	>=dev-python/appdirs[${PYTHON_USEDEP}]-1.4.4
	')
"
BDEPEND="
	${RDEPEND}
	$(python_gen_cond_dep '
	test? (
		>=dev-python/pytest[${PYTHON_USEDEP}]-8.4.1
		)
	')
"

src_prepare() {
	default

	rm requirements.txt build.sh
}

# src_compile() {
# 	python_optimize "${S}"
# }

src_test() {
	"${EPYTHON}" -m pytest -v || die "Tests failed"
}

src_install() {

}
