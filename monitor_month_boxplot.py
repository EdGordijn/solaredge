import pandas as pd
import solaredge

import matplotlib.pyplot as plt

from ssdtools.branding import plot_style

    
# Stel de style in
plot_style(style='MER2020:1', margins=False)

# Get solardata
api_key = '0JZ8Q9LPBWIQ4KJHV8XJ2D1STNQA3MHH'
site_id = '2752001'

start_time = '2022-04-01 00:00:00'
end_time = '2022-04-10 23:59:59'

s = solaredge.Solaredge(api_key)

sdata = s.get_power(site_id,
                    start_time=start_time,
                    end_time=end_time)

# Convert to dataframe
df = pd.DataFrame(sdata['power']['values'])

# Split date and time
df['date'] = pd.to_datetime(df['date'])
df['time'] = df['date'].dt.strftime('%H:%M')
df['date'] = df['date'].dt.strftime('%Y-%m-%d')

# Reshape 
df = df.pivot(index='time', columns='date', values='value')

# Time between 4:00 and 22:00
df = df.iloc[4*4:23*4+1]

#%% plot
fig, ax = plt.subplots()
fig.set_size_inches(10, 4)
# fig.subplots_adjust(top=0.85)
fig.suptitle('Vermogen gedurende de dag', fontsize=16)

df.T.boxplot(flierprops = dict(marker='.', 
                               markerfacecolor='#9491AA', 
                               markersize=2,
                               linestyle='none',
                               markeredgecolor='#9491AA'))

# Skip labels
ax.set_xticks(ax.get_xticks()[::4])

# Set ylim
ax.set_ylim(0, 2500)

# Set xlim
xlim = ax.get_xlim()
ax.set_xlim(xlim[0]+0.5, xlim[1]-.5)

# plt.show()


fname='monitor_month.png'
fig.savefig(fname, dpi=600)