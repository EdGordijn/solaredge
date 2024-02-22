import solaredge
from datetime import datetime, time, timedelta
from calendar import monthrange
import json

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from get_greenchoice_data import GreenchoiceApi


#%% Get solardata
today = datetime.now() #.date()
start_date = today.replace(day=1)
end_date = today

# start_date = datetime(2024, 1, 1)
# end_date = datetime(2024, 1, 31)

with open('/home/edgordijn/solaredge.json', 'r') as json_file:
    userinfo = json.load(json_file)

s = solaredge.Solaredge(userinfo['api_key'])
panels = s.get_energy_details_dataframe(userinfo['site_id'],
                                        start_time=start_date,
                                        end_time=end_date)

# Index as date
panels.index = panels.index.date

# Energy in kWh
panels['Production'] /= 1000

#%% Get meterstanden
greenchoiche = GreenchoiceApi(username=userinfo['username'],
                              password=userinfo['password'])

###TODO automatiseer het jaar
df2 = greenchoiche.get_meterstanden(year=2024, product=1)

# Results per day
df2 = df2.sort_values(by=['OpnameDatum'], ascending=True)
df2['levering'] = -(df2['StandNormaal'] + df2['StandDal']).diff(periods=-1)
df2['teruglevering'] = -(df2['TerugleveringNormaal'] + df2['TerugleveringDal']).diff(periods=-1)


#%% Merge data
df3 = df2.join(panels)

df3['zon'] = df3['Production'] - df3['teruglevering']

#%% plot
plt.style.use('myplotstyle')

fig, ax = plt.subplots()
fig.set_size_inches(10, 4)
# fig.suptitle('Maandopbrengst', fontsize=16)

# Colors, mark current day
# df['colors'] = '#B68CB8'
# df.loc[df.index[-1], 'colors'] = '#6461A0'

df3['teruglevering'] *= -1

ax.bar(df3.index,
       'levering', #'teruglevering'],
       data=df3,
       # color=df['colors'],
       label='Levering')
        # label=f'{start_date.strftime("%Y-%m")} {energy:6.1f} kWh'.replace(' ', u'\u2007')                                               )

ax.bar(df3.index,
        'zon',
        bottom='levering',
        data=df3,
        # color=df['colors'],
        label='Zon')
        # label=f'{start_date.strftime("%Y-%m")} {energy:6.1f} kWh'.replace(' ', u'\u2007')                                               )

ax.bar(df3.index,
       'teruglevering',
       data=df3,
       # color=df['colors'],
       label='Teruglevering')
        # label=f'{start_date.strftime("%Y-%m")} {energy:6.1f} kWh'.replace(' ', u'\u2007')                                               )

# # Markerlines and text for statistics
# stats = {'min': df['value'].min(),
#          'max': df['value'].max(),
#          'mean': df['value'].mean()}

# for label, y in stats.items():
#     ax.axhline(y, color='#314CB6', lw=0.5, marker='None', zorder=1)
#     ax.annotate(f'{label} {y:.1f} kWh',
#                 xy=(1, y), xycoords=("axes fraction", "data"),
#                 xytext=(5, 0), textcoords='offset points',
#                 va='center')

# Set yaxis label
ax.set_ylabel('energy in kWh')

# Set xtick labels to appear every 15 minutes
xlocator = mdates.DayLocator()
ax.xaxis.set_major_locator(xlocator)

# Format xtick labels as daynumbers
formatter = mdates.DateFormatter('%a\n%d')
ax.xaxis.set_major_formatter(formatter)

# Set xlim
# start_date = datetime(start_date.year, start_date.month, start_date.day, 0, 0)
start_date = datetime.combine(start_date, time(0, 0))
end_date = datetime.combine(end_date, time(0, 0))

# last_day = start_date.replace(day=monthrange(today.year, today.month)[1])
# last_day = end_date
last_day = end_date.replace(day=monthrange(end_date.year, end_date.month)[1])

ax.set_xlim(start_date - timedelta(hours=12),
            last_day + timedelta(hours=12))

# Gridlines
ax.grid(axis='x')

# legend
ax.legend(loc='lower right', bbox_to_anchor=(1, 1))

# Save figure
fig.savefig(fname='fig/monitor_month.png', dpi=600)

# Geschat jaarverbruik
df3 = df3.dropna(subset=['Production'])
dagen = len(df3.index)
verwacht_jaarverbruik = (df3.levering.sum() + df3.zon.sum()) / dagen * 365

print(f'Het verwacht jaarverbruik na {dagen} dagen: {verwacht_jaarverbruik:.0f}')


#%% Pie chart

# pie_data = df3[['levering','teruglevering', 'zon']].sum(axis=0)
# pie_data['teruglevering'] *= -1

# pie_data.plot.pie()