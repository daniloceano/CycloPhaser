
Procedure Overview
==================

The **CycloPhaser** program identifies distinct phases of cyclone life cycles by analyzing the relative vorticity time series at the cyclone center and its first derivative. This method enables precise detection of four main stages: **incipient**, **intensification**, **mature**, and **decay**. 

1. **Preprocessing and Filtering**: Initially, users can apply a Lanczos filter to the vorticity series to remove noise that could interfere with detecting cyclone stages. For smoother results, a Savitzky-Golay filter is used twice on the data.
  
2. **Phase Detection**: The program automatically identifies peaks and valleys in the smoothed vorticity data, which represent key life cycle phases. These phases include:
   - **Incipient Stage**: Detected from unassigned periods at the beginning of the cyclone life cycle.
   - **Intensification Stage**: Marked by an increase in vorticity from one peak to a subsequent valley.
   - **Mature Stage**: Identified between specific vorticity valleys and peaks, representing the cyclone’s peak strength.
   - **Decay Stage**: Detected as the decrease in vorticity after the mature phase until the system dissipates.

3. **Residual Stage**: This stage accounts for systems that re-intensify without progressing to maturity due to tracking limitations.


.. figure:: cyclophaser_methodology.jpg
   :scale: 50%
   :align: center

   **Figure**: A brief overview of the CycloPhaser methodology showing how the program detects and labels different cyclone life cycle phases.

CycloPhaser’s automated approach allows for high-efficiency analysis of thousands of cyclones, making it suitable for large climatological studies.

For more detailed information, you can refer to the original publication: Couto de Souza et al. (2024). *New perspectives on South Atlantic storm track through an automatic method for detecting extratropical cyclones' lifecycle*. International Journal of Climatology.