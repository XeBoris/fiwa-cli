# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# Read version from pyproject.toml
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python 3.10 and earlier

with open(os.path.abspath('../../pyproject.toml'), 'rb') as f:
    pyproject = tomllib.load(f)
    version = pyproject['project']['version']
    release = version

project = 'FiWa-CLI'
copyright = '2026, Boris Bauermeister'
author = 'Boris Bauermeister'
# version and release are now set from pyproject.toml above

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # For Google/NumPy style docstrings
    'sphinx.ext.viewcode',  # Add source code links
    'sphinx.ext.intersphinx',  # Link to other projects' docs
    'sphinx_autodoc_typehints',  # Better type hint support
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'  # ReadTheDocs theme
html_static_path = ['_static']

# Napoleon settings for better docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Add intersphinx mapping for cross-references
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'textual': ('https://textual.textualize.io', None),
}