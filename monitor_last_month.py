import pandas as pd
import solaredge
from datetime import datetime, timedelta
from calendar import monthrange

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


#%% Get solardata
api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

today = datetime.now()
start_date = datetime(2022, 3, 1)
end_date = today - timedelta(days=1)

s = solaredge.Solaredge(api_key)

sdata = s.get_energy(site_id,
                     start_date=start_date.date(),
                     end_date=end_date.date(),
                     time_unit='DAY')

# Convert to dataframe
df = pd.DataFrame(sdata['energy']['values'])
df['time'] = pd.to_datetime(df['date'])
df['value'] /= 1000

energy = df['value'].sum()

#%% plot
plt.style.use('myplotstyle')

fig, ax = plt.subplots()
fig.set_size_inches(10, 4)
# fig.suptitle('Maandopbrengst', fontsize=16)                     

ax.plot('time',
        'value',
        data=df,
        color='#6461A0',
        marker='o',
        label=f'{today.year} {energy:6.1f} kWh'.replace(' ', u'\u2007')
                                                 )

# Markerlines and text for statistics
stats = {'min': df['value'].min(),
         'max': df['value'].max(),
         'mean': df['value'].mean()}

for label, y in stats.items():
    ax.axhline(y, color='#314CB6', lw=0.5, marker='None', zorder=1)
    ax.annotate(f'{label} {y:.1f} kWh',
                xy=(1, y), xycoords=("axes fraction", "data"),
                xytext=(5, 0), textcoords='offset points',
                va='center')

# Set yaxis label
ax.set_ylabel('energy in kWh')

# Set xtick labels to appear every 15 minutes
# xlocator = mdates.DayLocator()
xlocator = mdates.AutoDateLocator()
ax.xaxis.set_major_locator(xlocator)

# Format xtick labels as Daynumber and month year on second row
formatter = mdates.ConciseDateFormatter(xlocator)
# formatter.zero_formats[2] = '%d' # start with day 
# formatter.offset_formats[2] = '%B %Y'
# formatter.offset_formats[2] = 'April %Y' # avoid english month names
ax.xaxis.set_major_formatter(formatter)
    
# Set xlim
last_day = today.replace(day=monthrange(today.year, today.month)[1])
ax.set_xlim(start_date - timedelta(hours=12),
            last_day + timedelta(hours=12))

# Gridlines
ax.grid(axis='x')

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.savefig(fname='monitor_last_month.png', dpi=600)