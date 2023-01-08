#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 15:22:39 2022

@author: edgordijn

Test opvragen meteodata
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, time, timedelta
from calendar import monthrange

import solaredge
from ssdtools.meteo import Meteo

today = datetime.now().date()
start_date = today.replace(day=1)
end_date = today

start_date = datetime(2022, 10, 1)
end_date = datetime(2022, 11, 9)

#%% Get solardata
api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

s = solaredge.Solaredge(api_key)

sdata = s.get_energy(site_id,
                     start_date=start_date.strftime('%Y-%m-%d'),
                     end_date=end_date.strftime('%Y-%m-%d'),
                     time_unit='DAY')

# Convert to dataframe
df = pd.DataFrame(sdata['energy']['values'])
df['time'] = pd.to_datetime(df['date'])
df['opgewekt'] = df['value']/1000

energy = df.loc[df.index[:-1], 'value'].sum()

# Data van het KNMI
meteo = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                        end=end_date.strftime('%Y%m%d'),
                        vars='SQ:Q',
                        stns=215)

# Bereken de zonuren
zonuren = meteo.data.groupby(['YYYYMMDD'])[['SQ', 'Q']].sum()
zonuren['SQ'] /= 10

# Convert datum
zonuren.index = pd.to_datetime(zonuren.index, format='%Y%m%d')
zonuren = zonuren.reset_index()

#%% plot
plt.style.use('myplotstyle')

fig, ax1 = plt.subplots()
fig.set_size_inches(10, 4)

ax1.bar('time',
        'opgewekt',
         data=df,
         label='energie')

# Second y-axis
ax2 = ax1.twinx()
ax2.bar('YYYYMMDD',
        'Q',
        data=zonuren,
        width=0.3,
        label='straling',
        color='orange')


# ax1.set_zorder(1)
# ax1.set_frame_on(False)

# Set yaxis label
ax1.set_ylabel('opgewekt [kWh]')
ax2.set_ylabel('straling')

# Set xtick labels to appear every 15 minutes
xlocator = mdates.DayLocator()
ax1.xaxis.set_major_locator(xlocator)

# Format xtick labels as daynumbers
formatter = mdates.DateFormatter('%d')
ax1.xaxis.set_major_formatter(formatter)
    
# Set xlim
start_date = datetime.combine(start_date, time(0, 0))
end_date = datetime.combine(end_date, time(0, 0))

last_day = end_date.replace(day=monthrange(end_date.year, end_date.month)[1])

ax1.set_xlim(start_date - timedelta(hours=12),
             last_day + timedelta(hours=12))

# Gridlines
ax1.grid(axis='x')

# legend
ax1.legend(loc='lower left', bbox_to_anchor=(0, 1))
ax2.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.savefig(fname='zonuren.png', dpi=600)

#%% Plot energie versus zonnestraling

fig2, ax = plt.subplots()
fig2.set_size_inches(10, 4)

ax.scatter(zonuren['Q'],
           df.opgewekt,
           s=2,
           clip_on=False,
           zorder=10)

# Lineair fit
X = np.vstack([zonuren['Q'], np.zeros(len(zonuren.index))]).T
a, _, _, _ = np.linalg.lstsq(X, df.opgewekt, rcond=-1)

x = range(1400)
ax.plot(x,
        a[0]*x,
        color='orange',
        linewidth=1)

# Set xlim
ax.set_xlim(0, 1400)
ax.set_ylim(0, 16)

# Set axis labels
ax.set_xlabel('straling')
ax.set_ylabel('opgewekt [kWh]')

# No margins
ax.margins(0)

# Save figure
fig2.savefig(fname='energie_zonuren.png', dpi=600)


