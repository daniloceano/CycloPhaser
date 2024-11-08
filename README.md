
# CycloPhaser: A Python Package for Detecting Extratropical Cyclone Life Cycles

[![Documentation Status](https://readthedocs.org/projects/cyclophaser/badge/?version=latest)](https://cyclophaser.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/cyclophaser.svg)](https://badge.fury.io/py/cyclophaser)
[![PyPI Downloads](https://pepy.tech/badge/cyclophaser)](https://pepy.tech/project/cyclophaser)
[![CircleCI](https://circleci.com/gh/daniloceano/CycloPhaser.svg?style=shield)](https://circleci.com/gh/daniloceano/CycloPhaser)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Versions](https://img.shields.io/pypi/pyversions/cyclophaser)](https://pypi.org/project/cyclophaser/)

CycloPhaser is a package designed to automate and improve the accuracy of detecting and categorizing cyclone life cycle phases, including intensification, maturation, and decay. Understanding these phases is crucial for analyzing cyclone behavior and the dynamic processes that drive their development. This knowledge supports both operational forecasters and researchers focused on improving cyclone representation in numerical models, ultimately enhancing forecast accuracy. Traditionally, phase identification requires manual analysis, which introduces subjectivity and limits the feasibility of analyzing large datasets. CycloPhaser addresses these challenges by offering an efficient, objective approach, compatible with high-resolution reanalysis data and real-time observations alike. With CycloPhaser, users gain a powerful tool for cyclone life cycle classification, supporting both advanced meteorological research and practical forecasting applications.

CycloPhaser is described in detail in the paper by de Souza et al. (under review) and has been used to generate results presented by de Souza et al. (2024).

![CycloPhaser Example Plot](https://github.com/daniloceano/CycloPhaser/raw/master/docs/_images/test_custom.png)

**Important Note**: CycloPhaser requires cyclone tracking data as input but does not perform cyclone tracking itself. There are various cyclone tracking algorithms available in the literature. Walker et al. (2020) provide a discussion on these methods, while open-source tracking tools, such as [CyTRACK](https://github.com/apalarcon/CyTRACK) by Pérez-Alarcón et al. (2024), are publicly accessible. Additionally, cyclone track databases, like the [Atlantic extratropical cyclone tracks database]((https://data.mendeley.com/datasets/kwcvfr52hp/4)) by Gramcianinov et al. (2020), are available for use.


## Installation

1. Install using pip

   ```
   pip install cyclophaser


## Documentation

For detailed documentation, visit the [CycloPhaser Documentation](https://cyclophaser.readthedocs.io/en/latest/). This includes function parameters, module descriptions, and more.

# Support and Contact

For support, feature requests, or any queries, please open an issue on the GitHub repository.

# License

This project is licensed under the GNU General Public License v3.0. You may obtain a copy of the license at https://www.gnu.org/licenses/gpl-3.0.html.


### References

- de Souza, D. C., da Silva Dias, P. L., Gramcianinov, C. B., & de Camargo, R. (under review). *CycloPhaser: A Python Package for Detecting Extratropical Cyclone Life Cycles*. Journal of Open Source Software.
  
- de Souza, D. C., da Silva Dias, P. L., Gramcianinov, C. B., da Silva, M. B. L., & de Camargo, R. (2024). New perspectives on South Atlantic storm track through an automatic method for detecting extratropical cyclones' lifecycle. *International Journal of Climatology*, 44(10), 3568-3588.

- Gramcianinov, C. B., Campos, R. M., de Camargo, R., Hodges, K. I., Guedes Soares, C., & da Silva Dias, P. L. (2020). Atlantic extratropical cyclone tracks in 41 years of ERA5 and CFSR/CFSv2 databases. *Mendeley Data*, 4, 108111.

- Pérez-Alarcón, A., Coll-Hidalgo, P., Trigo, R. M., Nieto, R., & Gimeno, L. (2024). CyTRACK: An open-source and user-friendly Python toolbox for detecting and tracking cyclones. *Environmental Modelling & Software*, 176, 106027.

- Walker, E., Mitchell, D. M., & Seviour, W. J. (2020). The numerous approaches to tracking extratropical cyclones and the challenges they present. *Weather*, 75(11), 336-341.
