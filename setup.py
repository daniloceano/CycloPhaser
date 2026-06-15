from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

VERSION = '2.0.0'
DESCRIPTION = 'Determine phases from extratropical cyclone life cycle'

setup(
    name="cyclophaser",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Danilo Couto de Souza",
    author_email="danilo.oceano@gmail.com",
    license='GPL-3.0-or-later',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        "cmocean>=4.0",
        "contourpy>=1.3",
        "cycler>=0.12",
        "fonttools>=4.53",
        "iniconfig>=2.0",
        "kiwisolver>=1.4",
        "matplotlib>=3.9",
        "numpy>=2.1",
        "packaging>=24.1",
        "pandas>=2.2",
        "pillow>=10.4",
        "pluggy>=1.5",
        "pyparsing>=3.1",
        "python-dateutil>=2.9",
        "pytz>=2024.2",
        "scipy>=1.14",
        "setuptools>=72",
        "six>=1.16",
        "tzdata>=2024.1",
        "wheel>=0.44",
        "xarray>=2024.9"
    ],
    extras_require={
        'test': ['pytest>=8.3'],
    },
    package_data={
        'cyclophaser': ['example_data/example_file.csv'],
    },
    keywords=['cyclone', 'vorticity', 'meteorology', 'atmospherical sciences'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
    ],
    project_urls={
        'Documentation': 'https://cyclophaser.readthedocs.io/en/latest/',
        'Source Code': 'https://github.com/daniloceano/CycloPhaser',
        'Issue Tracker': 'https://github.com/daniloceano/CycloPhaser/issues',
    },
)
