# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'CycloPhaser'
copyright = '2023, Danilo Couto de Souza'
author = 'Danilo Couto de Souza'
release = '2.1.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
# No html_static_path: docs/_static/ is git-ignored, so a clean checkout (Read the
# Docs) has no such folder and Sphinx warns. Generated files live in docs/generated/.

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.extlinks']

# Links into the repository (research records, the calibration app's README,
# the CHANGELOG). One place for the branch they point to.
REPO_BLOB = 'https://github.com/daniloceano/CycloPhaser/blob/master/'
extlinks = {'repo': (REPO_BLOB + '%s', '%s')}