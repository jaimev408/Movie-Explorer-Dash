import time
import numpy as np
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

#functions
def dataClean(data):
    data.loc[((data.Rated == "Unrated") | (data.Rated == "13") | (data.Rated == "6") | (data.Rated == "15") | (data.Rated == "14") |
         (data.Rated == "18") | (data.Rated == "12") | (data.Rated == "15") | (data.Rated == "15")), "Rated"] = "Not Rated"
    data.loc[(data.Rated == "X"), "Rated"] = "NC-17"
    data.loc[((data.Rated == "Atp") | (data.Rated == "All") | (data.Rated == "U")), "Rated"] = "G"
    data.loc[(data.Rated == "M"), "Rated"] = "TV-MA"
    data.loc[(data.Rated == "PG13"), "Rated"] = "PG-13"
    data.loc[((data.Rated == "15A") | (data.Rated == "12A") | (data.Rated == "MA15+") |  (data.Rated == "AL")), "Rated"] = "Other"
    data.Rated = data.Rated.fillna("Not Rated")


    genres = np.unique(np.concatenate(data.Genre.value_counts().index.str.split(", ")))
    genres = genres[(genres != "PG-13") & (genres != "Not Rated") & (genres != "G") & (genres != "TV-MA") & (genres != "NC-17")].tolist()
    genres.insert(0, "All")
    
    ratings = np.unique(data.Rated).tolist()
    ratings.insert(0, "All")
    
    yearsChoice = np.sort((data['Year'].unique()))  
    increments = (max(yearsChoice) - min(yearsChoice))/4
    sliderMarks = {
        str(min(yearsChoice)): str(min(yearsChoice)),
        str(int(min(yearsChoice) + increments)): int(min(yearsChoice) + increments),
        str(int(min(yearsChoice) + increments * 2)): int(min(yearsChoice) + increments * 2),
        str(int(min(yearsChoice) + increments * 3)): int(min(yearsChoice) + increments * 3),
        str(max(yearsChoice)): str(max(yearsChoice)),
        }
    
    return data, genres, sliderMarks, ratings
    
#Resources
external_stylesheets = [dbc.themes.BOOTSTRAP]
data, genres, sliderMarks, ratings = dataClean(pd.read_csv("../app/resources/all_movies.csv"))


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll',
    }
}

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("Filters", className="display-4"),
        html.P("Please choose a filter", className="lead"),
        html.Hr(),
        dbc.Nav(
            [
                html.Label('Film Genre', id='genre--label'),
                dcc.Dropdown(
                id='genreDropdown',
                options=[{'label': genre, 'value': genre} for genre in genres],
                value='All'
                ),
                html.Hr(),
                html.Div(id='output-container-range-slider'),    
                html.Hr(),
                dcc.RangeSlider(
                    id='year-range--slider',
                    min=data['Year'].min(),
                    max=data['Year'].max(),
                    value=[data['Year'].min(),data['Year'].max()],
                    marks=sliderMarks,
                    updatemode='drag',
                    allowCross=False,
                    pushable=True),
                html.Hr(),
                html.Label('Film Rating', id='rating--label'),
                dcc.Dropdown(id='rating--dropdown',                
                     options=[{'label': rating, 'value': rating} for rating in ratings],                
                     value='All'),
                 html.Hr(),
            
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

main_layout = html.Div([
    dcc.Tabs(id='tabs-example', value='tab-1', children=[
        dcc.Tab(label='Rating', value='tab-1'),
        dcc.Tab(label='Rotten', value='tab-2'),
    ]),
    
    html.Div([
        dbc.Spinner(html.Div([
            dcc.Graph(id='tabs-example-content'),
            ]),
        size='lg')
    ])
    #html.Div(id='tabs-example-content'),
    ], 
    style=CONTENT_STYLE,)
                           
app.layout = html.Div([dcc.Location(id="url"), sidebar, main_layout])


@app.callback(
    dash.dependencies.Output('output-container-range-slider', 'children'),
    [dash.dependencies.Input('year-range--slider', 'value')])
def update_output(value):
    return 'Film Years: ' + str(value[0]) +' to '+ str(value[1])

@app.callback(Output('tabs-example-content', 'figure'),
              [Input('tabs-example', 'value'),
              Input('genreDropdown', 'value'),
              Input('year-range--slider', 'value'),
              Input('rating--dropdown', 'value')])
def render_content(tab, genre, years, rating):
    finalData = data
    #clean up format for money
    finalData["BoxOfficeStr"] = finalData.BoxOffice.fillna("No Data")
    finalData.loc[finalData['Image'] == 'fresh', "Image"] = "certified"
    yaxis = "BoxOffice"    
    if tab == 'tab-1':
        xaxis = "Rating10"
        hd = ["Title", "BoxOfficeStr", "Rating10", "Year"]
        ht = "<b>Rsting: %{x}</b><br>Average Box Office: %{y}<extra></extra>"
        htf = "<b>Title: %{customdata[0]}</b> <br><br>Box Office: %{customdata[1]} <br>Rating: %{customdata[2]}<br>Year: %{customdata[3]}<extra></extra>"
    elif tab == 'tab-2':
        xaxis = "Rotten"
        hd = ["Title", "BoxOfficeStr", "Rotten", "Year"]
        ht = "<b>Rotten: %{x}</b><br>Average Box Office: %{y}<extra></extra>"
        htf = "<b>Title: %{customdata[0]}</b> <br><br>Box Office: %{customdata[1]} <br>Rotten: %{customdata[2]}<br>Year: %{customdata[3]}<extra></extra>"
        
    if genre != "All":
        genresDF = finalData.Genre.str.split(", ", expand=True)
        finalData = finalData[(genresDF == genre).any(axis=1)]        
    
    finalData = finalData.loc[(finalData.Year >= years[0]) & (finalData.Year <= years[1])]
    
    if rating != "All":
        finalData = finalData.loc[finalData.Rated == rating]
    
    #fig = px.scatter(finalData, x=xaxis, y=yaxis, hover_data=['Title'])

    fig = px.histogram(
        finalData, x=xaxis, y=yaxis,
        marginal='rug',
        histfunc='avg',
        nbins=50,
        color = 'Image',
        barmode = 'overlay',
        opacity = 0.7,
        labels = {
            'Rating10': "Ratings",
            'BoxOffice': "Box Office Revenue"
            },
        title = 'Average Box Office Revenue vs Ratings',
        hover_data = hd
        )
    
    fig.update_traces(hovertemplate = ht,
                      selector=dict(type="histogram"))

    fig.update_traces(hovertemplate = htf,
                      selector=dict(type="box"))

    return fig

if __name__ == '__main__':
    app.run_server()
