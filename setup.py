from setuptools import setup, find_packages

VERSION = '1.4.2'
DESCRIPTION = 'Determine phases from extratropical cyclone life cycle'
LONG_DESCRIPTION = 'This script processes vorticity data, identifies different phases of the cyclone \
    and plots the identified periods on periods.png and periods_didatic.png'

setup(
    name="cyclophaser",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
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
    ]
)
