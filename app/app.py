import dash
from dash import Dash, dcc, html, dash_table, Input, Output, ctx, callback, State, ALL
from dash_extensions.javascript import assign, Namespace
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import requests
import pandas as pd
import geopy.distance
import json
import dash_leaflet.express as dlx
import ast
from ast import literal_eval

import shapely
from shapely import Polygon
from shapely import wkt
import json

#declare variables for initial use on app load


prop_U5 = 0.059
prop_att = 0.607


tab_style = {'font-family': 'Nunito, sans-serif', 'font-size': '14px', 'color': 'rgb(35, 22, 115)', 'font-weight': '700'}
style = dict(weight=0.25, opacity=1, color='blue', dashArray='3', fillOpacity=0.7)


#open route service api key
api_key = '5b3ce3597851110001cf6248794cc26b77c44bd6ba57adf491254f74'

#calling with requests
base_url = "https://api.openrouteservice.org/geocode/search?api_key="
directions_url = "https://api.openrouteservice.org/v2/directions/driving-car?api_key="

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
}

#territorial authorities
tas = ['Ashburton District',
 'Auckland',
 'Buller District',
 'Carterton District',
 "Central Hawke's Bay District",
 'Central Otago District',
 'Christchurch City',
 'Clutha District',
 'Dunedin City',
 'Far North District',
 'Gisborne District',
 'Gore District',
 'Grey District',
 'Hamilton City',
 'Hastings District',
 'Hauraki District',
 'Horowhenua District',
 'Hurunui District',
 'Invercargill City',
 'Kaikoura District',
 'Kaipara District',
 'Kapiti Coast District',
 'Lower Hutt City',
 'Mackenzie District',
 'Manawatu District',
 'Marlborough District',
 'Masterton District',
 'Matamata-Piako District',
 'Napier City',
 'Nelson City',
 'New Plymouth District',
 'Opotiki District',
 'Otorohanga District',
 'Palmerston North City',
 'Porirua City',
 'Queenstown-Lakes District',
 'Rangitikei District',
 'Rotorua District',
 'Ruapehu District',
 'Selwyn District',
 'South Taranaki District',
 'South Waikato District',
 'South Wairarapa District',
 'Southland District',
 'Stratford District',
 'Tararua District',
 'Tasman District',
 'Taupo District',
 'Tauranga City',
 'Thames-Coromandel District',
 'Timaru District',
 'Upper Hutt City',
 'Waikato District',
 'Waimakariri District',
 'Waimate District',
 'Waipa District',
 'Wairoa District',
 'Waitaki District',
 'Waitomo District',
 'Wellington City',
 'Western Bay of Plenty District',
 'Westland District',
 'Whakatane District',
 'Whanganui District',
 'Whangarei District']

#declare javascript functions for managing geoJSON objects
ns = Namespace('dashExtensions', 'default')

style_function = ns('style_handle')
locale_filter_function = ns('ta_filter')
marker_filter_function = ns('marker_filter')

#create geoJSON objects
locales = dl.GeoJSON(
                url='/assets/locales.geojson',
                options=dict(style=style_function),
                filter=(locale_filter_function),
                hideout=dict(style=style, ta=tas, over="False"),
                id='locales'
                )

markers_gj = dl.GeoJSON(
                url = '/assets/services.geojson',
                cluster=False,
                filter=(marker_filter_function),
                hideout=dict(ta='', view='', show="False", search='', lat=0, lng=0, dist=0),
                id='marker'
                )

custom_icon = dict(
    iconUrl='https://leafletjs.com/examples/custom-icons/leaf-green.png',
    shadowUrl='https://leafletjs.com/examples/custom-icons/leaf-shadow.png',
    iconSize=[38, 95],
    shadowSize=[50, 64],
    iconAnchor=[22, 94],
    shadowAnchor=[4, 62],
    popupAnchor=[-3, -76]
)

search_marker = dl.Marker(id='search-marker',position=[0,0], opacity=0, icon=custom_icon)

#load locale summary data
with open('app/assets/ta_summary.json') as fp:
    ta_summary = json.load(fp)

ta_summary_df = pd.DataFrame.from_dict(ta_summary, orient='index')[['total_ece_places','total_ece_pop', 'overall_ece_demand']]
ta_summary_df.rename(columns={"total_ece_places": "places", "total_ece_pop": "pop", "overall_ece_demand": "demand"}, inplace=True)
ta_summary_df.sort_values(by=['demand'], ascending=False, inplace=True)
ta_summary_df.reset_index(inplace=True, names='TA')

#create colour bar
colorbar = dlx.categorical_colorbar(categories=['over demand', 'near', 'under', 'no people'], colorscale=['red', 'orange', 'green', 'grey'], width=300, height=30, position="topright", opacity=0.3)

#helper function to create result card for a service
def create_result_card(name, lat, lng, type, max_places, free, U2s):

    card = html.Div(
                dbc.Card(
                    dbc.CardBody(
                        children=[ 
                            html.H6(name, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '700'}),
                            html.P(type, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'black', 'font-weight': '300'}),
                            dbc.Accordion(
                                dbc.AccordionItem([
                                    html.P("Approved child places: " + str(max_places), id='approved-places', style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    dbc.Tooltip("The amount of child places that the service is approved for.", target='approved-places'),
                                    html.P("Under 2 places: " + str(U2s), style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    html.P("20 Hours Free: " + free, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    ],
                                title="Show details",
                                style={'padding': '0px'}),
                                start_collapsed=True
                            )
                        ]
                    )
                    ), style={'margin': '20px'}
                )

    return card


# stylesheet with the .dbc class
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = html.Div([
    html.Div(
        [
        html.Div(id='locale-stats',
                 className='info',
                style={'position': 'absolute', 'top': '100px', 'right': '10px', 'zIndex': '1001'}),
        dbc.Offcanvas(
            [
            dbc.Tabs(
                [
                dbc.Tab([
                    html.Hr(),
                    dbc.Row([
                        dbc.Col(html.P("National ECE capacity "), width=9, style=style),
                        dbc.Col(html.P(id='national-capacity'), width=3)
                    ]),
                    dbc.Row([
                        dbc.Col(html.P("National ECE population "), width=9),
                        dbc.Col(html.P(id='national-population'), width=3)
                    ]),
                    dbc.Row([
                        dbc.Col(html.P("National ECE demand "), width=9),
                        dbc.Col(html.P(id='national-demand'), width=3)
                    ]),
                    dbc.Row([
                        dbc.Col(html.P("Localities over demand "), width=9),
                        dbc.Col(html.P(id='national-locales-over'), width=3)
                    ]),
                    html.Hr(),
                    html.Div([
                        dash_table.DataTable(
                            id='national-table',
                            columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in ta_summary_df],
                            data = ta_summary_df.to_dict('records'),
                            editable=False,
                            filter_action="none",
                            sort_action="native",
                            sort_mode="single",
                            column_selectable=False,
                            row_selectable=False,
                            row_deletable=False,
                            selected_columns=[],
                            selected_rows=[],
                            page_action="native",
                            page_current= 0,
                            page_size= 75,
                            style_data={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'font-family': 'system-ui',
                                    'font-size': '14px'
                                }
                            )])
                    ], label='National', tab_style=tab_style, tab_id='national_tab'),
                dbc.Tab([
                    html.Div([
                    html.Hr(),
                    dbc.Row([
                        dbc.Col(
                            dbc.Select(
                            id='ta-filter',
                            options=tas),
                            width=7
                            ),
                        html.Br(),
                        html.Br(),
                        dbc.Col(
                            dbc.Switch(id='service-marker-filter', label='show services', value=False),
                            width=5
                            )
                        ]),
                        dbc.Row(
                            dbc.Button("Clear", id="clear-ta-btn")  
                        ),
                        html.Hr(),
                        html.Div(id='results-card'),
                        html.Div(id="address-card"),
                        html.Div(id='search-results'),
                        html.P(id="service-name"),
                        html.P(id="distance"),
                        html.Div(id="marker_clicked"),
                        html.P(id='pop')
                        ])
                ], label='Locality', tab_style=tab_style, tab_id='locality_tab')],
                id='tabs',
                active_tab='national_tab'
            )
            ], id="offcanvas", title="ECE Service Demand Visualiser", is_open=True, backdrop=False
        )]
    ),
    html.Div([
        dl.Map(children = [
            dl.TileLayer(), 
            markers_gj, 
            search_marker,
            locales,
            colorbar],
           center = [-41.87057, 168.29466],
           zoom=6,
           style={'width' : '100%', 'height' : '100vh', 'margin' : 'auto', 'display' : 'block'},
           id="map"
        )]),
])


#national view
@app.callback(
        [Output('national-capacity', 'children'),
         Output('national-population', 'children'),
         Output('national-demand', 'children'),
         Output('national-locales-over', 'children'),
         Output('ta-filter', 'value', allow_duplicate=True)],
         [Input('national-capacity', 'children'),
          Input('national-table', 'active_cell'),
          Input('national-table', 'derived_virtual_data')],
          prevent_initial_call='initial_duplicate'
)
def national_view(capacity, selected_cell, derived_data):

    ta = None

    if(selected_cell is not None):
        clicked_row = selected_cell['row']

        ta = derived_data[clicked_row]['TA']

    national_capacity = 0
    national_pop = 0
    national_demand = 0
    national_locales = 0
    national_over_near = 0
    national_under = 0

    for key, value in ta_summary.items():
        national_capacity = national_capacity + value['total_ece_places']
        national_pop = national_pop + value['total_ece_pop']

        national_over_near = national_over_near + value['over_demand_locales'] + value['near_demand_locales']
        national_under = national_under + value['under_demand_locales']

        national_locales = national_locales + 1

    national_demand = round(national_pop/national_capacity, 2)

    return (national_capacity, national_pop, national_demand, national_over_near, ta)

#ta selected - update polygons and markers
@app.callback(
    [Output('locales', 'hideout'),
    Output('marker', 'hideout')],
    [Input('ta-filter', 'value'),
    Input('service-marker-filter', 'value')],
    [State('locales', 'hideout'),
    State('marker', 'hideout')],
    prevent_initial_call=True
)
def update_hideout(ta, service_filter, locale_hideout, marker_hideout):

    locale_hideout['ta'] = ta

    marker_hideout['ta'] = ta
    marker_hideout['show'] = str(service_filter)
    marker_hideout['search'] = ''
    marker_hideout['view'] = 'ta'

    return(locale_hideout, marker_hideout)

#update ta summary
@app.callback(
    Output('locale-stats', 'children'),
    Input('ta-filter', 'value'),
    prevent_initial_call=True
)
def update_ta_summary(ta):

    if (ta is not None):
        summary_details = ta_summary[ta]

        result = html.Div(children=[
            html.P(ta),
            html.P("Total ECE pop: " + str(summary_details['total_ece_pop'])),
            html.P('Total ECE places: ' + str(summary_details['total_ece_places'])),
            html.P('Overall ECE demand: ' +  str(summary_details['overall_ece_demand'])),
            html.P('Total localities: ' + str(summary_details['total_locales'])),
            html.P('Over demand locales: ' + str(summary_details['over_demand_locales'])),
            html.P('Near demand locales: ' + str(summary_details['near_demand_locales'])),
            html.P('Under demand locales: ' + str(summary_details['under_demand_locales'])),
            html.P('Total services: ' + str(summary_details['total_services'])),
        ])
        return(result)
    else:
        return ('Select a territorial authority')

#clear selected ta
@app.callback(
        [Output('ta-filter', 'value'),
         Output('service-marker-filter', 'value'),
         Output('results-card', 'children', allow_duplicate=True),
         Output('search-results', 'children', allow_duplicate=True),
         Output('tabs', 'active_tab')],
        Input('clear-ta-btn', 'n_clicks'),
        prevent_initial_call=True
)
def clear_ta(n_clicks):
    if(n_clicks is not None):
        return(None, False, None, None, 'national_tab')

#polygon clicked
@app.callback(
    [Output('results-card', 'children', allow_duplicate=True),
     Output('search-results', 'children', allow_duplicate=True),
     Output('tabs', 'active_tab', allow_duplicate=True)],
    Input('locales', 'n_clicks'),
    State('locales', 'clickData'),
    prevent_initial_call=True
)
def poly_click(n_clicks, feature):

    results_card = ''
    cards = []

    #check if a ta is selected
    if (feature is not None):


        #get the services for this ta
        services = feature['properties']['ece_services']

        total_places = 0
        total_services = 0

        #for each service, create a card to display it and increment total places and total services for the locale
        for service in services:
            card = create_result_card(service['name'], service['lat'], service['lng'], service['type'], service['max'], service['20_free'], service['U2s'])

            total_places = total_places + service['max']
            total_services = total_services + 1
            cards.append(card)

        if(feature['properties']['ece_capacity'] == 99):
            demand = 'There are no services in this area to meet demand.'
        elif(feature['properties']['ece_capacity'] == -1):
            demand = "There is no population in this locality."
        else:
            demand = 'ECE demand: ' + str(feature['properties']['ece_capacity'])

        results_card = html.Div(
            dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(feature['properties']['name'], style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '700'}),
                                html.Div('Total Early Learning centres: ' + str(total_services)),
                                html.Div('Total places available: ' + str(total_places)),
                                html.Div('Estimated ECE pop: ' + str(feature['properties']['ece_pop'])),
                                html.Br(),
                                html.Div(demand)
                            ]
                            )
                    ]
                    )
        )


    return(results_card, cards, 'locality_tab')


#run app
if __name__ == '__main__':
    app.run(debug=True)