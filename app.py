import requests
from dash import Dash, html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.io as pio
import numpy as np
import pandas as pd
import matplotlib as mpl
import gunicorn                     #whilst your local machine's webserver doesn't need this, Heroku's linux webserver (i.e. dyno) does. I.e. This is your HTTP server
from whitenoise import WhiteNoise   #for serving static files on Heroku

# plot theme
pio.templates.default = 'plotly_white'

# Instantiate dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/')

# Define Dash layout
def create_dash_layout(app):
    # Set browser tab title
    app.title = "InfoSparks Rough Draft" 
    
    # Header
    header = html.Div([dcc.Markdown(""" # InfoSparks data -> Newsletter skeleton.""")])
    
    # Body
    body = html.Div([dcc.Input(id="data-link"),
                    dcc.Graph(id="graph",
                              style={"width":"80%", "height":"600px"})
                     ])

    # Footer
    footer = html.Div([html.Div(id="info-dump")])

    # Assemble dash layout
    app.layout = html.Div([header, body, footer])

    return app

# Construct the dash layout
create_dash_layout(app)

# Callbacks

@app.callback(
    Output("graph", "figure"),
    Output("info-dump", "children"),
    Input("data-link", "value")
)
def make_graph(link):
    if link is not None:
        csv = requests.get(link)
        csv_r_split = csv.text.split("\r")
        len_csv_r_split = [len(x) for x in csv_r_split]
        data_index = len_csv_r_split.index(max(len_csv_r_split))

        title = csv_r_split[0]
        title = title.split(",")[-1]

        cols_csv = csv_r_split[data_index-1]
        cols = cols_csv.replace("\n", "").replace("\"" , "").split(",")[:-1]
        locations = cols[1:]

        df = pd.DataFrame(columns=["Date", title, "Location"])

        data_csv = csv_r_split[data_index]
        data_csv = data_csv.replace("$","")
        data = data_csv.split("\n")
        data = data[1:-1]
        data = [string.split(",")[:-1] for string in data]
        data = np.array(data).transpose()

        for i, loc in enumerate(locations):
            df = pd.concat([df, pd.DataFrame({'Date':data[0], title:data[i+1], "Location":loc})])

        df.reset_index(inplace=True)
        df.drop(columns='index', inplace=True)

        df = df.astype({"Date":str, title:float, 'Location':str})

        fig = px.line(df, x='Date', y=title, color='Location')
        fig.update_traces(mode="markers+lines", hovertemplate=None)
        fig.update_layout(hovermode='x unified')

    else:
        fig = px.line()
        df = pd.DataFrame()
    

    return fig, df.to_csv(index=False)





# Run flask app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8050)
