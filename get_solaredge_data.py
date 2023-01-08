#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 19 12:28:05 2022

@author: edgordijn
"""

import pandas as pd
from datetime import datetime

import solaredge


#%% Get solardata

start_date = datetime(2022, 3, 3)
end_date = datetime(2022, 11, 21)

api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

s = solaredge.Solaredge(api_key)

sdata = s.get_energy(site_id,
                     start_date=start_date.strftime('%Y-%m-%d'),
                     end_date=end_date.strftime('%Y-%m-%d'))

#%% Convert to dataframe
panels = pd.DataFrame(data=sdata['energy']['values'])

# Set date as index
panels = panels.set_index('date')
panels.index = pd.to_datetime(panels.index) # pd.to_datetime(panels['date'])

# Rename and use kWh as unit
panels['Production'] = panels['value']/1000
panels = panels.drop(['value'], axis=1)

#%% Alternative

panels2 = s.get_energy_details_dataframe(site_id, 
                                         start_time=start_date,
                                         end_time=end_date)

panels2['Production'] /= 1000
