
# APASVO v.0.0.1

A graphical tool to perform event detection/picking over a seismic trace.

Three different picking algorithms are available: STA-LTA, AMPA and Takanami


    STA-LTA algorithm processes seismic signals by using two moving time
    windows, a short time average window (STA), which measures the instant
    amplitude of the signal and watches for earthquakes, and a long time
    average windows, which takes care of the current average of the signal
    amplitude.

    See:
    Trnkoczy, A. (2002). Understanding and parameter setting of STA/LTA trigger
    algorithm. IASPEI New Manual of Seismological Observatory Practice, 2, 1-19.


    Adaptive Multi-Band Picking Algorithm (AMPA) method consists on an
    adaptive multi-band analysis that includes envelope detection, noise
    reduction for each band, and finally a filter stage that enhances the
    response to an earthquake arrival. This approach provides accurate
    estimation of phase arrivals in seismic signals strongly affected by
    background and non-stationary noises.
    
    See:
    Álvarez, I., García, L., Mota, S., Cortés, G., Benítez, C.,
    & De la Torre, A. (2013).
    An Automatic P-Phase Picking Algorithm Based on Adaptive Multiband Processing.
    Geoscience and Remote Sensing Letters, IEEE,
    Volume: 10, Issue: 6, pp. 1488 - 1492


    Takanami algorithm estimates the arrival time of a seismic signal
    by using two autoregressive models: a model that fits the earthquake and
    a noise model. Assuming that the characteristics before and after the
    arrival of the earthquake are quite different, the arrival time is
    estimated by searching the time point where the minimum value of the
    Akaike's Information Criterion is reached.

    See:
    Takanami, T., & Kitagawa, G. (1988).
    A new efficient procedure for the estimation of onset times of seismic
    waves. Journal of Physics of the Earth, 36(6), 267-290.


Created by Jose Emilio Romero Lopez.
Copyright 2013-2014.
