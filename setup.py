from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

VERSION = '2.1.3'
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
    python_requires=">=3.12",
    license_files=["LICENSE"],
    install_requires=[
        "cmocean>=4.0.3",
        "matplotlib>=3.9",
        "numpy>=2.1",
        "pandas>=2.2.2",
        "scipy>=1.14",
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
        "Programming Language :: Python :: 3.12",
    ],
    project_urls={
        'Documentation': 'https://cyclophaser.readthedocs.io/en/latest/',
        'Source Code': 'https://github.com/daniloceano/CycloPhaser',
        'Issue Tracker': 'https://github.com/daniloceano/CycloPhaser/issues',
    },
)
