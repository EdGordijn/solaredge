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
year_end = today - timedelta(days=1)

# For today the time period to monitor
start_time = time(4, 30)
end_time = time(22, 30)

# Combine date and time
today_start = datetime.combine(today.date(), start_time)
today_end = datetime.combine(today.date(), end_time)

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

# Total energy
energy_ytd = df_energy['value'].sum()


#%% plot setup
plt.style.use('myplotstyle')

fig, (ax1, ax2) = plt.subplots(2,1, gridspec_kw={'height_ratios': [2, 3]})
fig.set_size_inches(10, 6)

# set the spacing between subplots
plt.subplots_adjust(hspace=0.3)

# fig.suptitle('Maandopbrengst', fontsize=16)                     

#%% subplot 1: previous period

ax1.plot('time',
         'value',
         data=df_energy,
         color='#6461A0',
         linewidth=0.8,
         label=f'{today.year} {energy_ytd:6.1f} kWh'.replace(' ', u'\u2007'))

# Markerlines and text for statistics
# xlast = df_energy['time'].iloc[-1]
# ylast = df_energy['value'].iloc[-1]

# ax1.plot(xlast, ylast, marker='o', markersize=3, color='#6461A0')
# ax1.annotate(f'{xlast:%Y-%m-%d}',
#              xy=(xlast, ylast),
#              xytext=(10, 0), textcoords='offset points',
#              color='#6461A0',
#              ha='left',
#              bbox=dict(boxstyle="round4,pad=0.3",fc='white', ec='#6461A0',lw=0.5))


stats = {'min': df_energy['value'].min(),
         'max': df_energy['value'].max(),
         'mean': df_energy['value'].mean()}

xmax = df_energy.loc[df_energy['value'].idxmax(), 'time']
ymax = df_energy['value'].max()

ax1.plot(xmax, ymax, marker='o', color='#B68CB8')
ax1.annotate(f'{xmax:%Y-%m-%d}',
             xy=(xmax, ymax),
             xytext=(0, 10), textcoords='offset points',
             color='#B68CB8',
             ha='center',
             bbox=dict(boxstyle="round4,pad=0.3",fc='white', ec='#B68CB8',lw=0.5))

for label, y in stats.items():
    ax1.axhline(y, color='#314CB6', lw=0.5, marker='None', zorder=1)
    ax1.annotate(f'{label} {y:.1f} kWh',
                 xy=(1, y), xycoords=("axes fraction", "data"),
                 xytext=(5, 0), textcoords='offset points',
                 va='center')

# Set yaxis label
ax1.set_ylabel('energy in kWh')

# Set xtick labels to appear every month
ax1.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=16))
ax1.xaxis.set_major_formatter(ticker.NullFormatter())
ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    
# Set xlim
ax1.set_xlim(datetime(today.year, 1, 1),
             datetime(today.year, 12, 31))

# Set ytick labels
ylocator = ticker.MultipleLocator(5)
ax1.yaxis.set_major_locator(ylocator)

# legend
ax1.legend(loc='lower right', bbox_to_anchor=(1, 1))

#%% Subplot 2: current day

s = solaredge.Solaredge(api_key)

sdata = s.get_power(site_id,
                    start_time=today_start,
                    end_time=today_end)

# Convert to dataframe
df = pd.DataFrame(sdata['power']['values'])
df['time'] = pd.to_datetime(df['date'].str[11:]) # only time %H:%M:%S
df['value'] /= 1000

# Get total energy production
energy = s.get_energy(site_id,
                      start_date=today.date(),
                      end_date=today.date(),
                      time_unit='DAY')['energy']['values'][0]['value']
energy /= 1000

# Reference
ref = f'{xmax:%Y-%m-%d}' #'2022-05-15'

# Combine date and time
ref_start = datetime.combine(datetime.strptime(ref, '%Y-%m-%d'), start_time)
ref_end = datetime.combine(datetime.strptime(ref, '%Y-%m-%d'), end_time)

sdata_ref = s.get_power(site_id,
                        start_time=ref_start,
                        end_time=ref_end)

# Convert to dataframe
df2 = pd.DataFrame(sdata_ref['power']['values'])
df2['time'] = pd.to_datetime(df['date'].str[11:]) # only time %H:%M:%S
df2['value'] /= 1000

# Get total energy production
energy2 = s.get_energy(site_id,
                       start_date=ref,
                       end_date=ref,
                       time_unit='DAY')['energy']['values'][0]['value']
energy2 /= 1000


#%% plot

ax2.plot('time',
         'value',
         data=df2,
         linewidth=0.8,
         color='#B68CB8',
         label=f'{ref} {energy2:6.1f} kWh'.replace(' ', u'\u2007'))

ax2.plot('time',
         'value',
         data=df,
         color='#6461A0',
         # marker='o',
         label=f'{today.date()} {energy:6.1f} kWh'.replace(' ', u'\u2007'))


# Find maximum value
xmax = df.loc[df['value'].idxmax(), 'time'] 
ymax = df['value'].max()

# Markerlines
ax2.plot(xmax, ymax, marker='o', color='#314CB6')
# ax2.axvline(xmax, color='#314CB6', lw=0.5, marker='None', zorder=1)
ax2.axhline(ymax, color='#314CB6', lw=0.5, marker='None', zorder=1)

ax2.annotate(f'{xmax:%H:%M}',
             xy=(xmax, ymax), #xycoords="data",
             xytext=(0, 10), textcoords='offset points',
             color='#314CB6',
             ha='center',
             # arrowprops=dict(arrowstyle='-', color='#B68CB8'),
             bbox=dict(boxstyle="round4,pad=0.3",fc='white', ec='#314CB6',lw=0.5))

# Text
ax2.annotate(f'max {ymax:.1f} kW',
             xy=(1, ymax), xycoords=("axes fraction", "data"),
             xytext=(5, 0), textcoords='offset points',
             va='center')

# Set yaxis label
ax2.set_ylabel('power in kW')
  
# Set xtick labels to appear every hour
xlocator = mdates.HourLocator()
ax2.xaxis.set_major_locator(xlocator)

# Format xtick labels as HH:MM
xformatter = mdates.DateFormatter('%H:%M')
ax2.xaxis.set_major_formatter(xformatter)

# Set xlim
ax2.set_xlim(today_start, today_end)

# legend
ax2.legend(loc='lower right', bbox_to_anchor=(1, 1))

#%% Save figure
fig.savefig(fname='fig/monitor_new.png', dpi=600) 
