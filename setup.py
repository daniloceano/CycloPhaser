from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

VERSION = '1.8.1'
DESCRIPTION = 'Determine phases from extratropical cyclone life cycle'
# LONG_DESCRIPTION = 'This script processes vorticity data, identifies different phases of the cyclone \
    # and plots the identified periods on periods.png and periods_didatic.png'

setup(
    name="cyclophaser",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Danilo Couto de Souza",
    author_email="danilo.oceano@gmail.com",
    license='MIT',
    packages=find_packages(),
    install_requires=[],
    keywords=['cyclone', 'vorticity', 'meteorology', 'atmospherical sciences'],
    classifiers= [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3",
    ],
    project_urls={
        'Documentation': 'https://yourproject.readthedocs.io/en/latest/',
        'Source Code': 'https://github.com/daniloceano/CycloPhaser',
        'Issue Tracker': 'https://readthedocs.org/projects/cyclophaser/',
    },
)
