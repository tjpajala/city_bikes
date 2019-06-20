import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from analysis import aggregate_data, load_and_clean_data
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import pytz

from config import MAPBOX_ACCESS_TOKEN

desired_width = 640
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', 10)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions']=True

DATA_FOLDER = './data'
SOURCE_FILE = 'fillaridata.csv'

# load data
df = load_and_clean_data(DATA_FOLDER, SOURCE_FILE)

#aggregate data over time
agg_data = aggregate_data(df)


def get_dates(data, date_col='date'):
    return data[date_col].unique()


def get_hoverlabels(data, cols):
    return data[cols].apply(lambda row: ": ".join(row.values.astype(str)), axis=1)


def get_spaces(data):
    d = data.assign(space = lambda frame: (frame.bikesAvailable + frame.spacesAvailable))
    return d.groupby('name').agg({'space': min})

dates = get_dates(df, 'date')
times = [datetime.strftime(datetime.strptime("00:00:00","%H:%M:%S")+timedelta(minutes=10*x),"%H:%M")
         for x in range(int(24*60/10))]

#calculate number of spaces for each station, add to original df
spaces = get_spaces(df)
df["space"] = [spaces.loc[x][0] for x in df.name]


app.layout = html.Div([
    dcc.Tabs(id="tabs-selector", value="tab-1", children=[
        dcc.Tab(label="Overview by time", value="tab-1"),
        dcc.Tab(label="Individual station view", value="tab-2")
    ]),
    html.Div(id="tabs-component")

])


@app.callback(
    Output('tabs-component','children'),
    [Input('tabs-selector','value')]
)
def render_tabs(tab):
    if tab=='tab-1':
        return html.Div([
            html.H3("Overview of availability"),
            dcc.Graph(
                id='lat-long-available',
                style={'height': 600, 'width': 1200},
                animate=False

            ),
            html.Div([
                dcc.Slider(
                    id='date-slider',
                    min=0,
                    max=len(dates) - 1,
                    marks={i: {'label': str(dates[i]),
                               'style': {'color': 'red',
                                         "transform": "translateX(-0px) translateY(-70px) rotate(90deg)"
                                         }}
                           for i in range(len(dates))},
                    value=1
                ),
                dcc.Slider(
                    id="hour-slider",
                    min=0,
                    max=len(times) - 1,
                    marks={i: {'label': str(times[i]),
                               'style': {'color': 'red',
                                         "transform": "translateX(0px) translateY(0px) rotate(90deg)"
                                         }}
                           for i in range(len(times))},
                    value=3
                )
            ], style={'padding': 35})
        ])
    if tab == 'tab-2':
        return html.Div([
            html.H3('Individual station view'),
            # left side panel with map and slider
            html.Div([
                #html.H3('Tab content 2'),
                dcc.Graph(
                    id='lat-long-minimap',
                    animate=False

                ),
                dcc.Slider(
                    id='date-slider-tab2',
                    min=0,
                    max=len(dates) - 1,
                    marks={i: {'label': str(dates[i]),
                               'style': {'color': 'red',
                                         "transform": "translateX(-0px) translateY(-70px) rotate(90deg)"
                                         }}
                           for i in range(len(dates))},
                    value=1
                    )
            ], style={'height': "25%", 'width': "25%", 'display': 'inline-block'}),

            # main panel with graphs
            html.Div([
                dcc.Graph(id="daily-status-selected-station"),
            ], style={'height': "25%", 'width': "65%", 'display': 'inline-block'})
                    ])


@app.callback(
    Output('daily-status-selected-station','figure'),
    [Input('date-slider-tab2', 'value'),
     Input('lat-long-minimap','clickData')]
)
def update_daily_status(selected_date, clicked_station):
    if selected_date is None:
        selected_date = df.date.unique()[0]
    else:
        selected_date = dates[selected_date]

    if clicked_station is None:
        selected_station = "Porthania"
    else:
        selected_station = clicked_station["points"][0]["text"].split(":")[0]

    filtered_df = df[(df.date == selected_date) & (df.name == selected_station)]

    # we need to convert to UTC, because plotly autoconverts to utc time
    utc_zoned = [filtered_df.datetime.iloc[i].replace(tzinfo=pytz.timezone("UTC")) for i in range(len(filtered_df))]
    x = filtered_df.datetime.astype('str')
    y = filtered_df.bikesAvailable
    y2 = filtered_df.bikesAvailable / filtered_df.space * 100 #as percentage
    trace = go.Scatter(
        x=x,
        y=y,
        mode="lines+markers",
        line={'color': "blue"}
    )
    trace2 = go.Scatter(
        x = filtered_df.datetime.astype('str'),
        y=y2,
        mode="lines+markers",
        yaxis="y2",
        line={'color': "blue"}
    )
    return {
        'data': [trace, trace2],
        'layout': go.Layout(
            title=go.layout.Title(text=str(selected_station)),
            yaxis={'title': 'Number of bikes'},
            yaxis2={'title': 'Percentage of capacity',
                    'anchor': 'x',
                    'overlaying': 'y',
                    'side': 'right',
                    'position': 0.0},
            showlegend=False
        )
    }
@app.callback(
    Output('lat-long-minimap','figure'),
    [Input('date-slider-tab2', 'value')]
)
def update_minimap(selected_date):
    if selected_date is None:
        selected_date = df.date.unique()[0]
    else:
        selected_date = dates[selected_date]

    filtered_df = df[(df.date == selected_date)]
    print("selected date: " + str(selected_date))
    print("selected time: " + "no time on TAB2")
    print("rows: " + str(len(filtered_df)))
    trace = go.Scattermapbox(
        lon=filtered_df.lon,
        lat=filtered_df.lat,
        text=get_hoverlabels(filtered_df.round(3), ['name', 'bikesAvailable']).values,
        mode='markers',
        opacity=0.7,
        marker={
            'size': 15,
            'color': filtered_df['bikesAvailable'].values,
            'colorscale': [[0, 'rgba(178, 24, 43, 0.7)'],
                           [0.25, 'rgba(33, 102, 172, 0.7)'],
                           [1, 'rgba(33, 102, 172, 0.7)']],
            # 'colorscale': 'RdBu',
            'reversescale': False,
            'showscale': True
        }
    )

    return {
        'data': [trace],
        'layout': go.Layout(
            autosize=True,
            mapbox=go.layout.Mapbox(
                accesstoken=MAPBOX_ACCESS_TOKEN,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=df.lat.median(),
                    lon=df.lon.median()
                ),
                pitch=0,
                zoom=11
            ),
            xaxis={'title': 'Longitude'},
            yaxis={'title': 'Latitude'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }

@app.callback(
    Output('hour-slider','marks'),
    [Input('date-slider','value')]
)
def update_hour_slider_marks(selected_date):
    if selected_date is None:
        selected_date = df.date.unique()[0]
    else:
        selected_date = dates[selected_date]
    filtered_df = df[(df.date == selected_date)]
    available_times = filtered_df.time.unique()
    col = ['red' if x in available_times else 'lightgrey' for x in times]
    marks = {i: {'label': str(times[i]),
                 'style': {'color': col[i],
                           "transform": "translateX(-0px) translateY(0px) rotate(90deg)"
                           }}
             for i in range(len(times))}
    return marks
@app.callback(
    Output('lat-long-available', 'figure'),
    [Input('date-slider', 'value'),
     Input('hour-slider','value')])
def update_figure(selected_date, selected_time):
    if selected_date is None:
        selected_date = df.date.unique()[0]
    else:
        selected_date = dates[selected_date]

    if selected_time is None:
        selected_time = times
    else:
        selected_time = [times[selected_time]]
    filtered_df = df[(df.date == selected_date) & (df.time.isin(selected_time))]
    print("selected date: " + str(selected_date))
    print("selected time: " + str(selected_time))
    print("rows: " + str(len(filtered_df)))
    trace = go.Scattermapbox(
                    lon=filtered_df.lon,
                    lat=filtered_df.lat,
                    text=get_hoverlabels(filtered_df.round(3), ['name','bikesAvailable']).values,
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'color': filtered_df['bikesAvailable'].values,
                        'colorscale': [[0,'rgba(178, 24, 43, 0.7)'],
                                       [0.25, 'rgba(33, 102, 172, 0.7)'],
                                       [1, 'rgba(33, 102, 172, 0.7)']],
                        #'colorscale': 'RdBu',
                        'reversescale': False,
                        'showscale': True
                    }
                )

    return {
        'data': [trace],
        'layout': go.Layout(
                autosize=True,
                mapbox=go.layout.Mapbox(
                    accesstoken=MAPBOX_ACCESS_TOKEN,
                    bearing=0,
                    center=go.layout.mapbox.Center(
                        lat=df.lat.median(),
                        lon=df.lon.median()
                    ),
                    pitch=0,
                    zoom=11
                ),
                xaxis={'title': 'Longitude'},
                yaxis={'title': 'Latitude'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                legend={'x': 0, 'y': 1},
                hovermode='closest'
            )
    }


if __name__ == '__main__':
    app.run_server(debug=True)