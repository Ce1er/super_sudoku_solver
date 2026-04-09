EAPI=8

PYTHON_COMPAT=( python3_14 )

inherit python-single-r1 desktop

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
	>=dev-python/numpy-2.4.2[${PYTHON_USEDEP}]
	dev-python/pygments[${PYTHON_USEDEP}]
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

src_prepare() {
	default

	rm requirements.txt build.sh
}


python_test() {
	epytest
}


src_install() {
	PYTHON_MODULES="np_candidates sudoku save_manager techniques human_solver settings custom_types dlx_solver utils paths main"
	for mod in ${PYTHON_MODULES}; do
		python_domodule "${S}/src/${mod}.py"
	done

	python_newscript "${S}/src/main.py" "${PN}"
	python_newscript "${S}/src/save_manager.py" "${PN}-save-manager"
}
