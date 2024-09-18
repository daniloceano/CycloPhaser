---
title: 'CycloPhaser: A Python Package for Detecting Extratropical Cyclone Life Cycles from Vorticity Data'
tags:
  - Python
  - atmospheric science
  - meteorology
  - cyclones
authors:
  - name: Danilo Couto de Souza
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Institute of Astronomy, Geophysics, and Atmospheric Sciences, University of São Paulo (IAG-USP)
    index: 1
date: 2024-09-16
bibliography: paper.bib
---

# Summary

CycloPhaser is a Python package designed to detect and analyze extratropical cyclone life cycles from vorticity data. It enables researchers in meteorology and atmospheric sciences to automatically identify key stages of cyclone development, such as intensification, decay, and mature phases, using standardized methods. By leveraging vorticity data, CycloPhaser helps scientists study cyclones across various regions and timeframes, contributing to improved understanding of cyclone energetics and behavior.

# Statement of Need

Accurately identifying the regions where cyclones are positioned throughout their distinct life cycle stages remains a significant challenge in atmospheric sciences. Seminal works by [@bjerknes1922life], [@shapiro1990fronts], and [@neiman1993life] described extratropical cyclone life cycles in terms of structural changes and large-scale dynamics. However, these classifications were based on manual analysis of satellite imagery and synoptic charts, limiting their applicability to large datasets with multiple cyclone cases. Recent research has sought to objectively define cyclone life cycle stages using techniques such as normalizing the life cycle duration [@schemm2018during; @rudeva2007climatology] or bisecting the cycle into "intensification" and "decay" phases by focusing on periods before and after peak vorticity or the lowest central pressure [@dacre2009spatial; @trigo2006climatology; @azad2014vorticity; @booth2018extratropical; @michaelis2017changes]. While these approaches support the study of cyclone intensification and decay, they tend to overlook critical phases such as the incipient stage — where environmental dynamics are still adapting to the developing low-level disturbance and surface isobars are not yet fully closed. Additionally, they treat the mature phase as a single time step, failing to account for the possibility that it may encompass multiple time steps during which the cyclone exhibits homogeneous features.

The pioneering work by [@couto2024new] was the first to offer a comprehensive analysis of extratropical cyclone life cycles, dissecting systems into distinct life cycle phases and enabling the detection of multiple configurations across different systems. This study presents the Python package that facilitated such work. The method allows for an automated classification of cyclone life cycle stages, enabling the efficient processing of large datasets with minimal computational cost. This tool opens new avenues for research, such as analyzing cyclone life cycle behavior in climate change projections, enabling comparisons with present-day climates, and providing insights into how cyclone life cycles may evolve in response to climate variability. Additionally, it offers potential for assisting model validation by comparing the spatial positioning of life cycle phases across different models and reanalysis datasets. The package is both flexible and fully customizable, making it adaptable to a wide range of datasets and research needs.

# Features

The program includes optional pre-processing steps, such as applying a Lanczos filter to remove noise from the series and a Savitzky-Golay filter for smoothing, ensuring sinusoidal patterns in the data for phase detection. Key cyclone phases — intensification, decay, and mature — are identified through peaks and valleys in the vorticity time series. The intensification phase spans from a vorticity peak to the next valley, while the decay phase covers the opposite. The mature phase is defined as the period between a vorticity valley and neighboring derivative peaks. The pre-processing steps, as well as peaks and valleys detection in the vorticity series, are computed using Scipy's package [@virtanen2020scipy].

Thresholds for phase detection were rigorously calibrated using a representative set of cyclone tracks, ensuring accurate phase identification while filtering out noise. CycloPhaser also includes a residual phase to account for tracking anomalies, such as post-decay re-intensification without returning to maturity. A post-processing step further refines the phase boundaries by correcting gaps and isolating single time-step phases. Finally, the incipient stage is detected by missing labels in the series or by selecting the initial time steps. More details are discussed in [@couto2024new].

Although the program was initially devised for detecting life cycle phases using relative vorticity, it can be applied to any time series used as a proxy for cyclone detection, such as sea level pressure and geopotential height. Also, the program was designed for use in the Southern Hemisphere, but it can be applied to Northern Hemisphere vorticity series by multiplying by minus one.

# References
