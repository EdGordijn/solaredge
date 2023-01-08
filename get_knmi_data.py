#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 13 21:22:12 2022

@author: edgordijn
"""

from datetime import datetime
import pandas as pd

from ssdtools.meteo import Meteo
#%% Predict production based on previous radiation

start_date = datetime(1992, 1, 1)
end_date = datetime(2016, 4, 30)

# Get data in intervals of max one year
meteo_list = []
for year in range(start_date.year, end_date.year + 1):
    if year == start_date.year:
        start = start_date
    else:
        start = datetime(year, 1, 1)
    end = min(datetime(year, 12, 31), end_date)
    print(start.date(), end.date())

    # Data van het KNMI
    meteo_list.append(Meteo.from_knmi(start=start.strftime('%Y%m%d'), 
                                      end=end.strftime('%Y%m%d'),
                                      vars='Q',
                                      stns=210,
                                      hourly=False).data
                 )
    
meteo = pd.concat(meteo_list)