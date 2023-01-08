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
from datetime import datetime

import solaredge
from ssdtools.meteo import Meteo

def draw_text(ax, 
              text, 
              loc='lower right', 
              prop=dict(size=6),
              bboxstyle='round,pad=0.,rounding_size=0.2',
              linewidth=0.3):
    """
    Draw a text-box, anchored by the given location
    """
    from matplotlib.offsetbox import AnchoredText
    
    at = AnchoredText(text, loc=loc, prop=prop, frameon=True)
    at.patch.set_boxstyle(bboxstyle)
    at.patch.set_linewidth(linewidth)
    ax.add_artist(at)
    
#%% Get solardata

start_date = datetime(2022, 3, 3)
end_date = datetime(2022, 12, 31)

api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

s = solaredge.Solaredge(api_key)

panels = s.get_energy_details_dataframe(site_id, 
                                        start_time=start_date,
                                        end_time=end_date)
# Energy in kWh
panels['Production'] /= 1000


# Data van het KNMI
meteo = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                        end=end_date.strftime('%Y%m%d'),
                        vars='Q',
                        stns=215)

# Calculate daily radiation, global radiation (in J/cm2)
straling = meteo.data.groupby(['YYYYMMDD'])['Q'].sum()

# # Convert datum
# straling.index = pd.to_datetime(straling.index, format='%Y%m%d')


#%% Plot energie versus radiation

plt.style.use('myplotstyle')

fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

# Text box
draw_text(ax, 
          f'KNMI-data Voorschoten (stn 215)\n{start_date:%Y-%m-%d} - {end_date:%Y-%m-%d}',
          )

# Plot data
ax.scatter(straling,
           panels['Production'],
           s=2,
           clip_on=False,
           zorder=10)

# Lineair fit
X = np.vstack([straling, np.zeros(len(straling))]).T
a, _, _, _ = np.linalg.lstsq(X, panels['Production'], rcond=-1)

x = range(3200)
ax.plot(x,
        a[0]*x,
        color='orange',
        linewidth=1,
        label=f'y = {a[0]:.5f} * x')

# Set xlim
ax.set_xlim(0, 3200)
ax.set_ylim(0, 30)

# Set axis labels
ax.set_xlabel('globale straling [J/cm\u00b2]')
ax.set_ylabel('opgewekt [kWh]')

# No margins
ax.margins(0)

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.savefig(fname='fig/correlatie_knmi.png', dpi=600)

#%% Correlate stn 215 Voorschoten with stn 210 Valkenburg zh

start_date = datetime(2014, 8, 1)
end_date = datetime(2016, 4, 30)

meteo_210 = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                            end=end_date.strftime('%Y%m%d'),
                            vars='Q',
                            stns=210,
                            hourly=False).data

meteo_215 = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                            end=end_date.strftime('%Y%m%d'),
                            vars='Q',
                            stns=215,
                            hourly=False).data

meteo = pd.concat([meteo_210, meteo_215])

# # Convert datum
# meteo['YYYYMMDD'] = pd.to_datetime(meteo['YYYYMMDD'], format='%Y%m%d')

# Calculate daily radiation, global radiation (in J/cm2)
straling = meteo.groupby(['STN', 'YYYYMMDD'])['Q'].sum() * a[0]

# Plot
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

# Plot data
ax.scatter(straling.loc[210],
           straling.loc[215],
           s=2,
           clip_on=False,
           zorder=10)

# Lineair fit
X = np.vstack([straling.loc[210], np.zeros(len(straling.loc[210]))]).T
p, _, _, _ = np.linalg.lstsq(X, straling.loc[215], rcond=-1)

x = range(26)
ax.plot(x,
        p[0]*x,
        color='orange',
        linewidth=1,
        label=f'y = {p[0]:.5f} * x')

# Set axis labels
ax.set_xlabel('opgewekt - meteo Valkenburg [kWh]')
ax.set_ylabel('opgewekt - meteo Voorschoten [kWh]')

# No margins
ax.margins(0)

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.savefig(fname='fig/meteo_stations.png', dpi=600)

#%% Predict production per month
start_date = datetime(2022, 1, 1)
end_date = datetime(2022, 12, 31)

# Data van het KNMI
meteo = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                        end=end_date.strftime('%Y%m%d'),
                        vars='Q',
                        stns=215)

# Calculate daily radiation, global radiation (in J/cm2)
straling = meteo.data.groupby(['YYYYMMDD'])['Q'].sum()

# Convert datum
straling.index = pd.to_datetime(straling.index, format='%Y%m%d')

# Monthly sums
per_maand = pd.concat([straling.groupby(straling.index.month).sum() * a[0],
                       panels.groupby(panels.index.month)['Production'].sum()],
                       axis=1)

# Totals
realisatie = per_maand['Production'].sum()
prognose = per_maand['Q'].sum()

# Plot
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

width = 0.3
ax.bar(per_maand.index-width/2,
       per_maand['Q'],
       label=f'{prognose:.0f} kWh prognose',
       width=width)

ax.bar(per_maand.index+width/2,
       per_maand['Production'],
       label=f'{realisatie:.0f} kWh realisatie',
       width=width,
       color='orange')

# Set axis labels
ax.set_ylabel('opgewekt [kWh]')
ax.set_xticks(per_maand.index,
              labels=['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'])

# legend
ax.legend(loc='lower right', ncol=1, bbox_to_anchor=(1, 1))                      

# Save figure
fig.savefig(fname='fig/prognose_vs_realisate.png', dpi=600)

#%% Predict production based on previous radiation

start_date = datetime(1988, 1, 1)
end_date = datetime(2016, 4, 30)

meteo_210 = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                            end=end_date.strftime('%Y%m%d'),
                            vars='Q',
                            stns=210,
                            hourly=False).data
# Correction for difference with stn 215
meteo_210['Q'] *= p[0]

start_date = datetime(2016, 5, 1)
end_date = datetime(2022, 12, 31)

meteo_215 = Meteo.from_knmi(start=start_date.strftime('%Y%m%d'), 
                            end=end_date.strftime('%Y%m%d'),
                            vars='Q',
                            stns=215,
                            hourly=False).data

meteo = pd.concat([meteo_210, meteo_215])


# Calculate daily radiation, global radiation (in J/cm2)
straling = meteo.groupby(['YYYYMMDD'])['Q'].sum() * a[0]


# # Convert datum
# straling.index = pd.to_datetime(straling.index, format='%Y%m%d')

# Monthly sums
straling_per_maand = straling.groupby([straling.index.month, straling.index.year]).sum()
straling_per_maand.index.names = ['maand', 'jaar']

straling_per_maand = pd.DataFrame(straling_per_maand)

#%% Box plot
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

ax.bar(per_maand.index,
       per_maand['Q'],
       label=f'{realisatie:.0f} kWh realisatie',
       width=width,
       color='orange')

straling_per_maand.groupby(level='maand').boxplot(subplots=False, ax=ax)

# Set axis labels
ax.set_ylabel('opgewekt [kWh]')
ax.set_xticks(ax.get_xticks(),
              labels=['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'])

ax.figure.savefig('fig/boxplot.png', dpi=600)

# #%% Violin plot
# fig, ax = plt.subplots()
# fig.set_size_inches(10, 4)

# ax.bar(per_maand.index-1,
#        per_maand['Q'],
#        label=f'{realisatie:.0f} kWh realisatie',
#        width=width,
#        color='orange')

# # straling_per_maand.groupby(level='maand').boxplot(subplots=False, ax=ax)
# import seaborn as sb

# sb.violinplot(x = 'maand',
#               y = "Q",
#               data = straling_per_maand.reset_index(),
#               inner="stick",
#               ax=ax)

# # Set axis labels
# ax.set_xlabel('')
# ax.set_ylabel('opgewekt [kWh]')
# ax.set_xticks(ax.get_xticks(),
#               labels=['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'])


# ax.figure.savefig('violin.png', dpi=600)

#%% Yearly production

straling_per_jaar = straling.groupby(straling.index.year).sum()
straling_per_jaar.index.names=['jaar']

# Plot
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

straling_per_jaar.plot(x='jaar',
                       y='Q',
                       marker='o',
                       ax=ax)

# Set axis labels
ax.set_xlabel('')
ax.set_ylabel('opgewekt [kWh]')

# Markerline for the target - proposal SolarEnergy
target = 2932
ax.axhline(target, color='#314CB6', lw=0.5, marker='None', zorder=1)
ax.annotate(f'target {target:.0f} kWh',
            xy=(1, target), xycoords=("axes fraction", "data"),
            xytext=(5, 0), textcoords='offset points',
            va='center')

ax.figure.savefig('fig/historische_jaaropbrengst.png', dpi=600)

#%% Expected yearly distribution

# Daily stats
straling = pd.DataFrame(straling)
straling['jaar'] = straling.index.year
straling['maand'] = straling.index.month
straling['dag'] = straling.index.day

stats_per_dag = straling.groupby(['maand', 'dag'])['Q'].agg(['mean', 'sem'])
stats_per_dag['ci95_hi'] = stats_per_dag['mean'] + 1.96* stats_per_dag['sem']
stats_per_dag['ci95_lo'] = stats_per_dag['mean'] - 1.96* stats_per_dag['sem']

# Cumulative value
stats_per_dag['mean'] = stats_per_dag['mean'].cumsum()
stats_per_dag['ci95_hi'] = stats_per_dag['ci95_hi'].cumsum()
stats_per_dag['ci95_lo'] = stats_per_dag['ci95_lo'].cumsum()

# drop schrikkeljaar
stats_per_dag = stats_per_dag.drop((2,29))

# Production this year
panels['opgewekt'] = panels['Production'].cumsum()
energy_ytd = panels['opgewekt'].max()

panels['jaar'] = panels.index.year
panels['maand'] = panels.index.month
panels['dag'] = panels.index.day
panels_per_dag = panels.groupby(['maand', 'dag'])['opgewekt'].sum()

stats_per_dag = stats_per_dag.join(panels_per_dag)


# Complate the dates
stats_per_dag = stats_per_dag.reset_index()
stats_per_dag['jaar'] = 2022

stats_per_dag.index = pd.to_datetime({'year': stats_per_dag['jaar'],
                                      'month': stats_per_dag['maand'],
                                      'day': stats_per_dag['dag']})

# Plot
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

stats_per_dag.plot(y='mean',
                   ax=ax)
# stats_per_dag.plot(y='ci95_lo',
#                     color='orange',
#                     ax=ax)
# stats_per_dag.plot(y='ci95_hi',
#                     color='orange',
#                     ax=ax)
ax.fill_between(stats_per_dag.index,
                stats_per_dag['ci95_lo'],
                stats_per_dag['ci95_hi'],
                color='b',
                alpha=.1)

stats_per_dag.plot(y='opgewekt',
                   color='#6461A0',
                   # linewidth=0.8,
                   label=f'2022 {energy_ytd:6.1f} kWh'.replace(' ', u'\u2007'),
                   ax=ax)

# legend
ax.legend(loc='lower right', ncol=1, bbox_to_anchor=(1, 1))                      

ax.figure.savefig('fig/historische_jaarontwikkeling.png', dpi=600)
