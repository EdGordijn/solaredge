import pandas as pd
import solaredge
from datetime import datetime, time

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
    
# Stel de style in
plt.style.use('myplotstyle')


#%% Get solardata
api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

# Day and period to monitor
today = datetime.now().date()
start_time = time(4, 30)
end_time = time(22, 30)

# Combine date and time
today_start = datetime.combine(today, start_time)
today_end = datetime.combine(today, end_time)

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
                      start_date=today,
                      end_date=today,
                      time_unit='DAY')['energy']['values'][0]['value']
energy /= 1000

# Reference
ref = '2022-05-15'

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
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)
# fig.subplots_adjust(top=0.85)

# fig.suptitle('Vermogen gedurende de dag', fontsize=16)

ax.plot('time',
        'value',
        data=df2,
        linewidth=0.8,
        color='#B68CB8',
        label=f'{ref} {energy2:6.1f} kWh'.replace(' ', u'\u2007'))

ax.plot('time',
        'value',
        data=df,
        color='#6461A0',
        marker='o',
        label=f'{today} {energy:6.1f} kWh'.replace(' ', u'\u2007'))


# Find maximum value
xmax = df.loc[df['value'].idxmax(), 'time'] 
ymax = df['value'].max()

# Markerlines
ax.axvline(xmax, color='#314CB6', lw=0.5, marker='None', zorder=1)
ax.axhline(ymax, color='#314CB6', lw=0.5, marker='None', zorder=1)

# Text
ax.annotate(f'max {ymax:.1f} kW',
            xy=(1, ymax), xycoords=("axes fraction", "data"),
            xytext=(5, 0), textcoords='offset points',
            va='center')

# Set yaxis label
ax.set_ylabel('power in kW')
  
# Set xtick labels to appear every hour
xlocator = mdates.HourLocator()
ax.xaxis.set_major_locator(xlocator)

# Format xtick labels as HH:MM
xformatter = mdates.DateFormatter('%H:%M')
ax.xaxis.set_major_formatter(xformatter)

# Set xlim
ax.set_xlim(today_start, today_end)

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.savefig(fname='monitor_day.png', dpi=600)