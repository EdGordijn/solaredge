import numpy as np
import pandas as pd
from datetime import datetime
import json

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

import solaredge
from ssdtools.meteo import Meteo

#%% Solardata user info
with open('/home/edgordijn/solaredge.json', 'r') as json_file:
    userinfo = json.load(json_file)


s = solaredge.Solaredge(userinfo['api_key'])

#%% Historische jaaropbrengst

#%% Correlate KNMI data with solarpanel production

start_date = datetime(2022, 3, 3)
end_date = datetime(2022, 12, 31)

panels = s.get_energy_details_dataframe(userinfo['site_id'], 
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

# Lineair fit
X = np.vstack([straling, np.zeros(len(straling))]).T
a, _, _, _ = np.linalg.lstsq(X, panels['Production'], rcond=-1)

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

# Calculate daily radiation, global radiation (in J/cm2)
straling = meteo.groupby(['STN', 'YYYYMMDD'])['Q'].sum() * a[0]

# Lineair fit
X = np.vstack([straling.loc[210], np.zeros(len(straling.loc[210]))]).T
p, _, _, _ = np.linalg.lstsq(X, straling.loc[215], rcond=-1)

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

###TODO automatisch bepalen
stats_per_dag['jaar'] = 2023

stats_per_dag.index = pd.to_datetime({'year': stats_per_dag['jaar'],
                                      'month': stats_per_dag['maand'],
                                      'day': stats_per_dag['dag']})

#%% plot setup
plt.style.use('myplotstyle')

fig, ax = plt.subplots()
fig.set_size_inches(10, 5)
   

#%% Plot stats
ax.fill_between(stats_per_dag.index,
                stats_per_dag['ci95_lo'],
                stats_per_dag['ci95_hi'],
                color='#B68CB8',
                alpha=.15)

stats_per_dag.plot(y='mean',
                   color='#B68CB8',
                   linewidth=0.8,
                   ax=ax)

#%% Periods
today = datetime.now()
###TODO: fix for 1 jan
if today.year == 2022:
    start_date = datetime(2022, 3, 1)
else:
    start_date = datetime(today.year, 1, 1)   
end_date = today # - timedelta(days=1)

# Handmatige invoer
# year_start = datetime(2022, 3, 3)
# year_end = datetime(2022, 12, 31)
# today = year_end

#%% Get solardata

# Energy this year
df_energy = s.get_energy_details_dataframe(userinfo['site_id'], 
                                        start_time=start_date,
                                        end_time=end_date,
                                        time_unit='DAY')
# Energy in kWh
df_energy['Production'] /= 1000

df_energy['time'] = df_energy.index.date

# Cumulative value
df_energy['cum_production'] = df_energy['Production'].cumsum()

# Total energy
energy_ytd = df_energy['Production'].sum()

                 

#%% plot

ax.plot('time',
        'cum_production',
        data=df_energy,
        color='#6461A0',
        label=f'{today.year} {energy_ytd:6.0f} kWh'.replace(' ', u'\u2007'))

# Markerline for the target - proposal SolarEnergy
target = 2932
ax.axhline(target, color='#314CB6', lw=0.5, marker='None', zorder=1)
ax.annotate(f'target {target:.0f} kWh',
            xy=(1, target), xycoords=("axes fraction", "data"),
            xytext=(5, 0), textcoords='offset points',
            va='center')

# Mark percentages
for p in range(20, 200, 20):
    t = target/100 * p

    if t <= energy_ytd:  
        idx = df_energy['cum_production'].where(df_energy['cum_production'] > t).first_valid_index()
        
        xp = df_energy.loc[idx, 'time']
        yp = df_energy.loc[idx, 'cum_production']
        
        ax.plot(xp, yp, marker='o', color='#B68CB8')

        ax.annotate(f'{p}%',
                    xy=(xp, yp),
                    xytext=(-10, 0), textcoords='offset points',
                    color='#B68CB8',
                    ha='right',
                    bbox=dict(boxstyle="round4,pad=0.3",fc='white', ec='#B68CB8',lw=0.5))


# Last datapoint
xmax = df_energy.loc[df_energy['cum_production'].idxmax(), 'time']
ymax = df_energy['cum_production'].max()

ax.plot(xmax, ymax, marker='o', color='#B68CB8')
ax.annotate(f'{xmax:%Y-%m-%d - {100*ymax/target:0.0f}%}',
            xy=(xmax, ymax),
            xytext=(10, 0), textcoords='offset points',
            color='#B68CB8',
            ha='left',
            bbox=dict(boxstyle="round4,pad=0.3",fc='white', ec='#B68CB8',lw=0.5))

# Set yaxis label
ax.set_ylabel('energy in kWh')

# Set xtick labels to appear every month
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=16))
ax.xaxis.set_major_formatter(ticker.NullFormatter())
ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    
# Set xlim
ax.set_xlim(datetime(today.year, 1, 1),
            datetime(today.year, 12, 31))

# Set ylim
ax.set_ylim(0)

# Set ytick labels
ylocator = ticker.MultipleLocator(200)
ax.yaxis.set_major_locator(ylocator)

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.tight_layout()
fig.savefig(fname='fig/monitor_cum_year.png', dpi=600) 

#%% Box plot

# Monthly sums
straling_per_maand = straling.groupby([straling.index.month, straling.index.year]).sum()
straling_per_maand.index.names = ['maand', 'jaar']
straling_per_maand = pd.DataFrame(straling_per_maand)

panels_per_maand = df_energy.groupby(df_energy.index.month)['Production'].sum()
# panels_per_maand = panels_per_maand.reindex(range(1, 13))

fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

ax.bar(panels_per_maand.index,
       panels_per_maand,
       label=f'{panels_per_maand.sum():.0f} kWh realisatie',
       width=0.3,
       color='orange')

straling_per_maand.groupby(level='maand').boxplot(column='Q', subplots=False, ax=ax)

# data labels
means = straling_per_maand.groupby(level='maand')['Q'].median()
for index, mean in enumerate(means):
    ax.annotate(f'{mean:.0f}',
                xy=(index+1, mean), 
                xytext=(15, 0), textcoords='offset points',
                va='center',
                fontsize=6, color='green')
for index, productie in panels_per_maand.items():
    ax.annotate(f'{productie:.0f}',
                xy=(index, 0), 
                xytext=(0, 5), textcoords='offset points',
                ha='center',
                va='center',
                fontsize=6, color='white')
    
# Set axis labels
ax.set_ylabel('opgewekt [kWh]')
ax.set_xticks(ax.get_xticks(),
              labels=['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'])

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# save fig
fig.tight_layout()
ax.figure.savefig('fig/boxplot.png', dpi=600)
