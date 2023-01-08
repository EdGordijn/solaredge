import pandas as pd
import solaredge
from datetime import datetime, time, timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

#%% Periods
today = datetime.now()
###TODO: fix for 1 jan
if today.year == 2022:
    year_start = datetime(2022, 3, 1)
else:
    year_start = datetime(today.year, 1, 1)   
year_end = today # - timedelta(days=1)


#%% Get solardata
api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

s = solaredge.Solaredge(api_key)

# Energy this year
sdata = s.get_energy(site_id,
                     start_date=year_start.date(),
                     end_date=year_end.date(),
                     time_unit='DAY')

# Convert to dataframe
df_energy = pd.DataFrame(sdata['energy']['values'])
df_energy['time'] = pd.to_datetime(df_energy['date'])
df_energy['value'] /= 1000

# Cumulative value
df_energy['value'] = df_energy['value'].cumsum()

# Total energy
energy_ytd = df_energy['value'].max()


#%% plot setup
plt.style.use('myplotstyle')

fig, ax = plt.subplots()
fig.set_size_inches(10, 6)

# fig.suptitle('Maandopbrengst', fontsize=16)                     

#%% plot

ax.plot('time',
        'value',
        data=df_energy,
        color='#6461A0',
        # linewidth=0.8,
        label=f'{today.year} {energy_ytd:6.1f} kWh'.replace(' ', u'\u2007'))

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
        idx = df_energy['value'].where(df_energy['value'] > t).first_valid_index()
        
        xp = df_energy.loc[idx, 'time']
        yp = df_energy.loc[idx, 'value']
        
        ax.plot(xp, yp, marker='o', color='#B68CB8')

        ax.annotate(f'{p}%',
                    xy=(xp, yp),
                    xytext=(-10, 0), textcoords='offset points',
                    color='#B68CB8',
                    ha='right',
                    bbox=dict(boxstyle="round4,pad=0.3",fc='white', ec='#B68CB8',lw=0.5))


# Last datapoint
xmax = df_energy.loc[df_energy['value'].idxmax(), 'time']
ymax = df_energy['value'].max()

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

#%% Save figure
fig.savefig(fname='monitor_cum_year.png', dpi=600) 
