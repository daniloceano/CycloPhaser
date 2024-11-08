.. CycloPhaser documentation master file

Welcome to CycloPhaser's Documentation!
========================================


CycloPhaser is a package designed to automate and improve the accuracy of detecting and categorizing cyclone life cycle phases, including intensification, maturation, and decay. Understanding these phases is crucial for analyzing cyclone behavior and the dynamic processes that drive their development. This knowledge supports both operational forecasters and researchers focused on improving cyclone representation in numerical models, ultimately enhancing forecast accuracy. Traditionally, phase identification requires manual analysis, which introduces subjectivity and limits the feasibility of analyzing large datasets. CycloPhaser addresses these challenges by offering an efficient, objective approach, compatible with high-resolution reanalysis data and real-time observations alike. With CycloPhaser, users gain a powerful tool for cyclone life cycle classification, supporting both advanced meteorological research and practical forecasting applications.

CycloPhaser is described in detail in the paper by de Souza et al. (under review) and has been used to generate results presented by de Souza et al. (2024).

.. image:: _images/test_custom.png
    :alt: CycloPhaser Canonical Example Plot
    :align: center
    

**Important Note**: CycloPhaser requires cyclone tracking data as input but does not perform cyclone tracking itself. There are various cyclone tracking algorithms available in the literature. Walker et al. (2020) provide a discussion on these methods, while open-source tracking tools, such as `CyTRACK <https://github.com/apalarcon/CyTRACK>`_ by Pérez-Alarcón et al. (2024), are publicly accessible. Additionally, cyclone track databases, like the `Atlantic extratropical cyclone tracks database <https://data.mendeley.com/datasets/kwcvfr52hp/4>`_ by Gramcianinov et al. (2020), are available for use.

Contents:

.. toctree::
   :maxdepth: 2

   overview
   installation
   usage
   testing
   api
   contribute
   license

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

References
----------

- de Souza, D. C., da Silva Dias, P. L., Gramcianinov, C. B., & de Camargo, R. (under review). *CycloPhaser: A Python Package for Detecting Extratropical Cyclone Life Cycles*. Journal of Open Source Software.

- de Souza, D. C., da Silva Dias, P. L., Gramcianinov, C. B., da Silva, M. B. L., & de Camargo, R. (2024). New perspectives on South Atlantic storm track through an automatic method for detecting extratropical cyclones' lifecycle. *International Journal of Climatology*, 44(10), 3568-3588.

- Gramcianinov, C. B., Campos, R. M., de Camargo, R., Hodges, K. I., Guedes Soares, C., & da Silva Dias, P. L. (2020). Atlantic extratropical cyclone tracks in 41 years of ERA5 and CFSR/CFSv2 databases. *Mendeley Data*, 4, 108111.

- Pérez-Alarcón, A., Coll-Hidalgo, P., Trigo, R. M., Nieto, R., & Gimeno, L. (2024). CyTRACK: An open-source and user-friendly Python toolbox for detecting and tracking cyclones. *Environmental Modelling & Software*, 176, 106027.

- Walker, E., Mitchell, D. M., & Seviour, W. J. (2020). The numerous approaches to tracking extratropical cyclones and the challenges they present. *Weather*, 75(11), 336-341.



