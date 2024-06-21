#!/usr/bin/env python
# coding: utf-8

# HDB Dashboard Creation Workflow
import json
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# #### Setting up dates for data extraction
mths_2012_14 = list()
year = range(2013, 2015, 1)
months = range(1, 13, 1)

for yr in year:
    for month in months:
        month = str(month).zfill(2)
        mths_2012_14.append(f"{yr}-{month}")

mths_2015_16 = list()
year = range(2015, 2017, 1)

for yr in year:
    for month in months:
        month = str(month).zfill(2)
        mths_2015_16.append(f"{yr}-{month}")

mths_2017_onwards = list()
year = range(2017, 2030, 1)

for yr in year:
    for month in months:
        month = str(month).zfill(2)
        mths_2017_onwards.append(f"{yr}-{month}")

mth_filter = mths_2017_onwards.index('2024-06')
mths_2017_onwards = mths_2017_onwards[:mth_filter+1]

df_cols = ['month', 'town', 'floor_area_sqm',
           'flat_type', 'lease_commence_date', 'resale_price']
param_fields = ",".join(df_cols)

mth_2012_2014 = "?resource_id=d_2d5ff9ea31397b66239f245f57751537"
base_url = "https://data.gov.sg/api/action/datastore_search"
url = base_url + mth_2012_2014

# Making the API calls
latest_df = pd.DataFrame()
for mth in mths_2012_14:
    params = {
        "fields": param_fields,
        "filters": json.dumps({'month': mth}),
        "limit": 10000
    }
    response = requests.get(url, params=params)
    mth_df = pd.DataFrame(response.json().get("result").get("records"))
    latest_df = pd.concat([latest_df, mth_df], axis=0)

mth_2015_2016 = "?resource_id=d_ea9ed51da2787afaf8e51f827c304208"
base_url = "https://data.gov.sg/api/action/datastore_search"
url = base_url + mth_2015_2016

for mth in mths_2015_16:
    params = {
        "fields": param_fields,
        "filters": json.dumps({'month': mth}),
        "limit": 10000
    }
    response = requests.get(url, params=params)
    mth_df = pd.DataFrame(response.json().get("result").get("records"))
    latest_df = pd.concat([latest_df, mth_df], axis=0)

mth_2017 = "?resource_id=d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
base_url = "https://data.gov.sg/api/action/datastore_search"
url = base_url + mth_2017

for mth in mths_2017_onwards:
    params = {
        "fields": param_fields,
        "filters": json.dumps({'month': mth}),
        "limit": 10000
    }
    response = requests.get(url, params=params)
    mth_df = pd.DataFrame(response.json().get("result").get("records"))
    latest_df = pd.concat([latest_df, mth_df], axis=0)


# Data Processing for creating charts
df = latest_df.copy()
df['yr_q'] = [str(i) for i in pd.to_datetime(df['month']).dt.to_period('Q')]
df['count'] = 1
df.rename(columns={'resale_price': 'price'}, inplace=True)
df.price = df.price.astype(float)

# Create price categories
bins = [0, 300000, 500000, 800000, 1000000, 2000000]
labels = ["0-300k", "300-500k", "500-800k", "800k-1m", ">=1m"]
df["price_grp"] = pd.cut(df["price"], bins=bins, labels=labels, right=False)
price_grps = df['price_grp'].unique().tolist()
price_grps.sort()

price_grps_dict = dict()
price_grps_dict[price_grps[0]] = '#8BC1F7'
price_grps_dict[price_grps[1]] = '#06C'
price_grps_dict[price_grps[2]] = '#4CB140'
price_grps_dict[price_grps[3]] = '#F0AB00'
price_grps_dict[price_grps[4]] = '#C9190B'

chart_width = 1000
chart_height = 600
today = str(datetime.today().date())
note = f'Updated on {today}'


# My Graphs
# Home price distributions
period = 'yr_q'
med_prices = [{i.get(period): i.get('price')} for i in df.groupby(period)[
    'price'].median().reset_index().to_dict(orient='records')]
high_med_prices = [i for i in med_prices if list(i.values())[0] >= 500000]
high_med_prices = [list(i.keys())[0] for i in high_med_prices]

fig = go.Figure()
for p in df[period].drop_duplicates():
    if p not in high_med_prices:
        fig.add_trace(go.Box(
            y=df[df[period] == p].price,
            name=str(p),
            boxpoints='outliers',
            marker_color='#06C',
            line_color='#06C',
            showlegend=False
        ))
    else:
        fig.add_trace(go.Box(
            y=df[df[period] == p].price,
            name=str(p),
            boxpoints='outliers',
            marker_color='#C9190B',
            line_color='#C9190B',
            showlegend=False
        ))


fig.update_layout(
    title=f"Quarters - Public Home Price Distributions<br>{note}",
    yaxis={"title": "Home Prices"},
    xaxis={"title": "Quarters"},
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

fig.add_hrect(
    y0="1000000", y1=str(round(df.price.max(), 100)),
    fillcolor="LightSalmon", opacity=0.35, layer="below", line_width=0,
)

fig.add_shape(
    showlegend=True, type="circle",
    name='Median Prices < 0.5M',
    fillcolor='#06C',
    y0=1000000, y1=1000000, x0=0, x1=0,
)

fig.add_shape(
    showlegend=True, type="circle",
    name='Median Prices >= 0.5M',
    fillcolor='#C9190B',
    y0=1000000, y1=1000000, x0=0, x1=0,
)

with open('profile/assets/charts/qtr_boxplot.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()


period = 'month'
fig = go.Figure()

med_prices = [{i.get(period): i.get('price')} for i in df.groupby(period)[
    'price'].median().reset_index().to_dict(orient='records')]
high_med_prices = [i for i in med_prices if list(i.values())[0] >= 500000]
high_med_prices = [list(i.keys())[0] for i in high_med_prices]

mth_df = df[df.yr_q >= '2020Q1']
for p in mth_df[period].drop_duplicates():
    if p not in high_med_prices:
        fig.add_trace(go.Box(
            y=df[df[period] == p].price,
            name=str(p),
            boxpoints='outliers',
            marker_color='#06C',
            line_color='#06C',
            showlegend=False
        ))
    else:
        fig.add_trace(go.Box(
            y=df[df[period] == p].price,
            name=str(p),
            boxpoints='outliers',
            marker_color='#C9190B',
            line_color='#C9190B',
            showlegend=False
        ))

fig.update_layout(
    title=f'Months - Public Home Price Distributions<br>{note}',
    yaxis={"title": "Home Prices"},
    xaxis={"title": "Months"},
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

fig.add_hrect(
    y0="1000000", y1=str(round(df.price.max(), 100)),
    fillcolor="LightSalmon", opacity=0.35, layer="below", line_width=0,
)

fig.add_shape(
    showlegend=True, type="circle",
    name='Median Prices < 0.5M',
    fillcolor='#06C',
    y0=1000000, y1=1000000, x0=0, x1=0,
)

fig.add_shape(
    showlegend=True, type="circle",
    name='Median Prices >= 0.5M',
    fillcolor='#C9190B',
    y0=1000000, y1=1000000, x0=0, x1=0,
)

with open('profile/assets/charts/mth_boxplot.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

# Advanced Million Dollar Homes
period = 'yr_q'
df['mil'] = [1 if i >= 1000000 else 0 for i in df['price']]
for_plot = df.groupby([period, 'mil'])[
    'town'].count().reset_index().sort_values(period)
cal_ = for_plot.pivot_table(index=period, values='town',
                            columns='mil', margins=True,
                            aggfunc="sum").reset_index().fillna(0)

for i in [0, 1, 'All']:
    cal_[i] = cal_[i].astype(int)

cal_['proportion'] = [round(i, 2) for i in cal_[1] / cal_['All'] * 100]
cal_mil_ts = cal_[cal_[period] != 'All'].reset_index(drop=True)
cal_mil_ts.columns = [period, '0', 'million $ Trans',
                      'Total Trans', '% million Trans']

fig = make_subplots(specs=[[{"secondary_y": True}]])

title = f"Quarters - % of Million Dollar Homes & Total Homes Sold<br>{note}"
fig.add_trace(go.Scatter(
    x=cal_mil_ts[period],
    y=cal_mil_ts['% million Trans'],
    mode='lines+markers',
    name="%"),
    secondary_y=False)

fig.add_trace(go.Bar(
    x=cal_mil_ts[period],
    y=cal_mil_ts['0'],
    opacity=.4,
    name="Total Sales"),
    secondary_y=True)

fig.update_layout(
    title=title,
    hovermode="x unified",
    xaxis={"title": "Quarters"},
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

fig.update_yaxes(title_text="Million Dollar Homes / Total Home Sales (%)",
                 secondary_y=False)
fig.update_yaxes(title_text="Total Sales", secondary_y=True)

fig.add_hline(y=1, line_width=1.5, line_dash="dash", line_color="black")
fig.add_hline(y=1.5, line_width=1.5, line_dash="dash", line_color="red")

with open('profile/assets/charts/qtr_barline_chart.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

period = 'month'
df['mil'] = [1 if i >= 1000000 else 0 for i in df['price']]
for_plot = df[df.yr_q >= '2020Q1'].groupby(
    [period, 'mil'])['town'].count().reset_index().sort_values(period)
cal_ = for_plot.pivot_table(index=period, values='town',
                            columns='mil', margins=True,
                            aggfunc="sum").reset_index().fillna(0)

for i in [0, 1, 'All']:
    cal_[i] = cal_[i].astype(int)

cal_['proportion'] = [round(i, 2) for i in cal_[1] / cal_['All'] * 100]
cal_mil_ts = cal_[cal_[period] != 'All'].reset_index(drop=True)
cal_mil_ts.columns = [period, '0', 'million $ Trans',
                      'Total Trans', '% million Trans']

fig = make_subplots(specs=[[{"secondary_y": True}]])

title = f"Months - % of Million Dollar Homes & Total Homes Sold<br>{note}"
fig.add_trace(go.Scatter(
    x=cal_mil_ts[period],
    y=cal_mil_ts['% million Trans'],
    mode='lines+markers',
    name="%"),
    secondary_y=False)

fig.add_trace(go.Bar(
    x=cal_mil_ts[period],
    y=cal_mil_ts['0'],
    opacity=.4,
    name="Total Sales"),
    secondary_y=True)

fig.update_layout(
    title=title,
    hovermode="x unified",
    xaxis={"title": "Months"},
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

fig.update_yaxes(title_text="Million Dollar Homes / Total Home Sales (%)",
                 secondary_y=False)
fig.update_yaxes(title_text="Total Sales", secondary_y=True)

fig.add_hline(y=1, line_width=1.5, line_dash="dash", line_color="black")
fig.add_hline(y=1.5, line_width=1.5, line_dash="dash", line_color="red")
with open('profile/assets/charts/mth_barline_chart.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

# ### Stacked Bar Values
period = 'yr_q'
pg_plots = df.groupby([period, 'price_grp'])['count'].sum().reset_index()

fig = go.Figure()
data = list()
for i in pg_plots.price_grp.drop_duplicates().tolist():
    fig.add_trace(
        go.Bar(name=i,
               x=pg_plots[pg_plots.price_grp == i][period].tolist(),
               y=pg_plots[pg_plots.price_grp == i]['count'].tolist(),
               marker_color=price_grps_dict[i]
               ))

fig.update_layout(
    barmode='stack',
    xaxis={'title': 'Quarters'},
    yaxis={'title': 'Count'},
    hovermode="x unified",
    title=f"Quarters - Total Public Home Sales by Price Category<br>{note}",
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1
                ))

with open('profile/assets/charts/qtr_stack_bar_values.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

period = 'month'
pg_plots = df[df.yr_q >= '2020Q1'].groupby([period, 'price_grp'])[
    'count'].sum().reset_index()

fig = go.Figure()
data = list()
for i in price_grps:
    fig.add_trace(
        go.Bar(name=i,
               x=pg_plots[pg_plots.price_grp == i][period].tolist(),
               y=pg_plots[pg_plots.price_grp == i]['count'].tolist(),
               marker_color=price_grps_dict[i]
               ))

fig.update_layout(
    barmode='stack',
    xaxis={'title': 'Months'},
    yaxis={'title': 'Count'},
    hovermode="x unified",
    title=f"Months - Total Public Home Sales by Price Category<br>{note}",
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

with open('profile/assets/charts/mth_stack_bar_values.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

# Stacked Bar Percentage
period = 'yr_q'
pg_base = df.groupby(period)['count'].sum().reset_index()
pg_plots = df.groupby([period, 'price_grp'])['count'].sum().reset_index()
for_plot = pg_plots.merge(pg_base, on=period)
for_plot.columns = [period, 'price_grp', 'count', 'total']
for_plot['percent_count'] = [round(
    i * 100, 1) for i in for_plot['count'] / for_plot['total']]

fig = go.Figure()
data = list()
for i in price_grps:
    fig.add_trace(
        go.Bar(name=i,
               x=for_plot[for_plot.price_grp == i][period].tolist(),
               y=for_plot[for_plot.price_grp == i]['percent_count'].tolist(),
               marker_color=price_grps_dict[i]
               ))

fig.add_hline(y=50, line_width=1.5, line_dash="dash", line_color="purple")
fig.update_layout(
    barmode='stack',
    title=f"Quarters - % of Public Home Sales by Price Category<br>{note}",
    xaxis={'title': 'Quarters'},
    yaxis={'title': '%'},
    hovermode="x unified",
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

with open('profile/assets/charts/qtr_stack_bar_percent.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

period = 'month'
mth_df = df[df.yr_q >= '2020Q1']
pg_base = mth_df.groupby(period)['count'].sum().reset_index()
pg_plots = mth_df.groupby([period, 'price_grp'])['count'].sum().reset_index()
for_plot = pg_plots.merge(pg_base, on=period)
for_plot.columns = [period, 'price_grp', 'count', 'total']
for_plot['percent_count'] = [round(
    i * 100, 1) for i in for_plot['count'] / for_plot['total']]

fig = go.Figure()
data = list()
for i in price_grps:
    fig.add_trace(
        go.Bar(name=i,
               x=for_plot[for_plot.price_grp == i][period].tolist(),
               y=for_plot[for_plot.price_grp == i]['percent_count'].tolist(),
               marker_color=price_grps_dict[i]
               ))

fig.add_hline(y=50, line_width=1.5, line_dash="dash", line_color="purple")
fig.update_layout(
    barmode='stack',
    title=f"Months - % of Public Home Sales by Price Category<br>{note}",
    xaxis={'title': 'Months'},
    yaxis={'title': '%'},
    hovermode="x unified",
    width=chart_width, height=chart_height,
    legend=dict(orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1)
)

with open('profile/assets/charts/mth_stack_bar_percent.html', 'w') as f:
    f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
f.close()

# Update time of code run
f = open("run_data.txt", "w")
f.write(str(datetime.today()))
f.close()
