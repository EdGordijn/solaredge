import solaredge
import pandas as pd
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

start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)


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

df2 = greenchoiche.get_meterstanden(year=start_date.year, product=1)

# Results per day
df2 = df2.sort_values(by=['OpnameDatum'], ascending=True)
df2['levering'] = -(df2['StandNormaal'] + df2['StandDal']).diff(periods=-1)

df2['teruglevering_normaal'] = -df2['TerugleveringNormaal'].diff(periods=-1)
df2['teruglevering_dal'] = -df2['TerugleveringDal'].diff(periods=-1)
df2['teruglevering'] = -(df2['TerugleveringNormaal'] + df2['TerugleveringDal']).diff(periods=-1)

# Corrigeer voor reset van meterstanden
df2.loc[df2['levering'] < 0] = 0
df2.loc[df2['teruglevering'] < 0] = 0

#%% Merge data
df3 = df2.join(panels)

df3['zon'] = df3['Production'] - df3['teruglevering']
df3 = df3.dropna(subset=['Production'])

print(f'{df3["levering"].sum():4.0f} kWh levering'.replace(' ', u'\u2007'))
print(f'{df3["zon"].sum():4.0f} kWh zon'.replace(' ', u'\u2007'))
print(f'{df3["teruglevering"].sum():4.0f} kWh teruglevering'.replace(' ', u'\u2007'))

#%% Tarieven
tarieven = pd.read_csv('tarieven.txt', 
                       comment='#',
                       date_format={'datum':'%Y-%m-%d'},
                       parse_dates=['datum'],
                       skipinitialspace=True,
                       index_col='datum')

df4 = pd.merge_asof(df3,
                    tarieven,
                    left_index=True,
                    right_index=True,
                    )

# Opbrengs met salderingsregeling 
df4['dal'] = df4.index.dayofweek > 4
df4['euro_teruglevering_dal'] = df4['teruglevering_dal'] * df4['tarief_dal']
df4['euro_teruglevering_normaal'] = df4['teruglevering_normaal'] * df4['tarief_normaal']
df4['euro_teruglevering_totaal'] = df4['euro_teruglevering_normaal'].fillna(0) + df4['euro_teruglevering_dal'].fillna(0)

df4.loc[df4['dal'], 'euro_zon_dal'] = df4['zon'] * df4['tarief_dal']
df4.loc[~df4['dal'], 'euro_zon_normaal'] = df4['zon'] * df4['tarief_normaal']
df4['euro_zon_totaal'] = df4['euro_zon_normaal'].fillna(0) + df4['euro_zon_dal'].fillna(0)

df4['euro_dal_totaal'] = df4['euro_zon_dal'] + df4['euro_teruglevering_dal']
df4['euro_normaal_totaal'] = df4['euro_zon_normaal'] + df4['euro_teruglevering_normaal']
df4['euro_totaal'] = df4['euro_zon_totaal'] + df4['euro_teruglevering_totaal']


print('tarief             zon  teruglevering         totaal')
print('-------- -------------  -------------  -------------')
print(f'dal     {df4["euro_zon_dal"].sum():14.0f} {df4["euro_teruglevering_dal"].sum():14.0f} {df4["euro_dal_totaal"].sum():14.0f}'.replace(' ', u'\u2007'))
print(f'normaal {df4["euro_zon_normaal"].sum():14.0f} {df4["euro_teruglevering_normaal"].sum():14.0f} {df4["euro_normaal_totaal"].sum():14.0f}'.replace(' ', u'\u2007'))
print('-------- -------------  -------------  -------------')
print(f'totaal  {df4["euro_zon_totaal"].sum():14.0f} {df4["euro_teruglevering_totaal"].sum():14.0f} {df4["euro_totaal"].sum():14.0f}'.replace(' ', u'\u2007'))


#%% plot
plt.style.use('myplotstyle')

fig, ax = plt.subplots()
fig.set_size_inches(10, 4)

df3['teruglevering'] *= -1

ax.bar(df3.index,
       'levering',
       data=df3,
       label=f'{df3["levering"].sum():4.0f} kWh levering'.replace(' ', u'\u2007'))

ax.bar(df3.index,
        'zon',
        bottom='levering',
        data=df3,
        label=f'{df3["zon"].sum():4.0f} kWh zon'.replace(' ', u'\u2007'))

ax.bar(df3.index,
       'teruglevering',
       data=df3,
       label=f'{-df3["teruglevering"].sum():4.0f} kWh teruglevering'.replace(' ', u'\u2007'))

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
start_date = datetime.combine(start_date, time(0, 0))
end_date = datetime.combine(end_date, time(0, 0))
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
dagen = len(df3.index)
verwacht_jaarverbruik = (df3.levering.sum() + df3.zon.sum()) / dagen * 365

print(f'Het verwacht jaarverbruik na {dagen} dagen: {verwacht_jaarverbruik:.0f}')


#%% Pie chart

pie_data = df3[['levering','zon', 'teruglevering']].sum(axis=0)
pie_data['teruglevering'] *= -1

pie_data.plot.pie()