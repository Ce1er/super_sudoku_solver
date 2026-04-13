# Version of ebuild to use
EAPI=9

# python3.14 is the only compatible version
PYTHON_COMPAT=( python3_14 )

# Tell distutils project is PEP517 complient
DISTUTILS_USE_PEP517=setuptools
inherit distutils-r1 

# Provides domenu command
inherit desktop

DESCRIPTION="Application to help solve sudoku puzzles"
HOMEPAGE="https://github.com/Ce1er/super_sudoku_solver"

# This is a live ebuild. It will fetch the HEAD of the git repository
# instead of a specific release.
inherit git-r3
EGIT_REPO_URI="https://github.com/Ce1er/super_sudoku_solver.git"

# Unstable on amd64 (AKA x86_64) (all unofficial gentoo packages are typically marked unstable)
# At the time of writing this Gentoo officially supports 10 other CPU architectures 
# https://wiki.gentoo.org/wiki/Handbook:Main_Page#Architectures
# Since I haven't tested my program on any other architectures it is bad practice to list them as supported.
KEYWORDS="~amd64"

LICENSE="BSD-4"

# Portage supports several versions of a package being installed if they are in different slots
# My program is designed to have only one version installed so if other ebuilds were made
# for specific versions of my program they would have the same slot.
SLOT="0"

# This shows that the test FEATURE can be used with this ebuild
IUSE="test"

# This will force a python interpreter from PYTHON_COMPAT to be used
# If several interpreters were in PYTHON_COMPAT then this would allow the program to be installed
# for each of those simultaneously. There isn't a good reason to do this besides testing
# but since it is possible it shouldn't be restricted.
REQUIRED_USE="${PYTHON_REQUIRED_USE}"


# Runtime dependencies
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

# Build dependencies
BDEPEND="
	${RDEPEND}
	$(python_gen_cond_dep '
	test? (
		>=dev-python/pytest-8.4.1[${PYTHON_USEDEP}]
		)
	')
"

# The above would be sufficient to install the program as distutils-r1 handles PEP517 
# projects very well. But there's a couple extra things I want Portage to do.

# If "test" FEATURE is enabled run tests and only install program if they all pass
distutils_enable_tests pytest


src_install() {
  # This would usually be ran by default but since I'm overwriting src_install it must be called directly
  # It will install super_sudoku_solver as a module in /usr/lib/python3.14/site-packages/super_sudoku_solver/
  # and byte compile it to improve performance.
  # It will also install /usr/bin/super-sudoku-solver which is defined as a gui-script in pyproject.toml.
  # As this is in $PATH and is executable it can be ran directly with the command `super-sudoku-solver`.
	distutils-r1_src_install

  # Install desktop file to /usr/share/applications/
  # S is the path to the directory Portage unpacks sources
	domenu "${S}/super-sudoku-solver.desktop"
}

# Show message after installation
# Portage usually manages system wide installation
# These commands are user specific so are not Portage's responsibility to run
pkg_postinst() {
	elog "Default puzzles can be generated with the following command:"
	elog "$ super-sudoku-solver --restore-default-puzzles"
	elog " "
	elog "A skeleton configuration file can be written using the following command"
	elog "$ super-sudoku-solver --restore-default-config"
}
