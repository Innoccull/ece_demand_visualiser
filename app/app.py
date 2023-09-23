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

#open route service api key
api_key = '5b3ce3597851110001cf6248794cc26b77c44bd6ba57adf491254f74'

#calling with requests
base_url = "https://api.openrouteservice.org/geocode/search?api_key="
directions_url = "https://api.openrouteservice.org/v2/directions/driving-car?api_key="

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
}

#import data
services = pd.read_csv("data\\ece_services_pop.csv")

lat = -41.87057
lng = 173.29466

prop_U5 = 0.059
prop_att = 0.607

style = dict(weight=0.25, opacity=1, color='white', dashArray='3', fillOpacity=0.7)


#create geoJSON objects
ns = Namespace('dashExtensions', 'default')

geojson = dl.GeoJSON(
                url='/assets/locales.geojson',
                options=dict(style=ns('style_handle')),
                hideout=dict(style=style),
                id='locales'
                )
markers_geojson = dl.GeoJSON(
    url='/assets/services.geojson',
    cluster=True,
    id='geo_markers'
)

#create result card for a service
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
    html.Div([
        dcc.Store('markers'),
        dcc.Store('markers_geojson'),
        dcc.Store('clicked_marker'),
        dcc.Store('demand'),
        dcc.Store('polygons')
        ]),
    html.Div(
        [
        html.Div(id='locale',
                 className='info',
                style={'position': 'absolute', 'top': '10px', 'right': '10px', 'zIndex': '1001'}),
        dbc.Offcanvas(
            [
            dbc.Row([
                dbc.Col(
                    dbc.Input(type="text", 
                    id="address_input",
                    placeholder="Enter a location",
                    persistence=False,
                    autocomplete="off"),
                    width=9),
                dbc.Col(
                    dbc.Button("Search", id="search_button"),
                    width=3
                    )
                ]),
                html.Br(),
                html.Div([
                dbc.Row([
                    dcc.Slider(1, 15, step=None, marks={
                        1: '1km',
                        2: '2km',
                        3: '3km',
                        4: '4km',
                        5: '5km',
                        10: '10km',
                        15: '15km'
                    }, 
                    id='distance-slider',
                    value=10)
                ]),
                html.Hr(),
                html.Div(id='results-card'),
                html.Div(id="address-card"),
                html.Div(id='search-results'),
                html.P(id="service-name"),
                html.P(id="distance"),
                html.Div(id="marker_clicked"),
                html.P(id='pop'),
                ])
            ], id="offcanvas", title="ECE Service Demand Visualiser", is_open=True, backdrop=False
        )]
    ),
    html.Div([
        dl.Map(children = [
            dl.TileLayer(), 
            geojson,
            markers_geojson],
           id="map", 
           center = (lat, lng),
           style={'width' : '100%', 'height' : '100vh', 'margin' : 'auto', 'display' : 'block'}
        )]),
])

#get directions - takes in a source and destination and returns a set of coordinates
def get_directions(source, destination):

    query = directions_url + api_key + "&start=" + source + "&end=" + destination

    call = requests.get(query, headers=headers)
    data = call.json()

    data = call.json()
    route = data['features'][0]['geometry']['coordinates']

    for coord in route:
        coord.reverse()

    return(route)

#update markers
@app.callback(
        [Output('markers', 'data', allow_duplicate=True),
         Output('demand', 'data')],
        [Input('search_button', 'n_clicks')],
        [State(component_id='address_input', component_property='value'),
         State(component_id='distance-slider', component_property='value')],
         prevent_initial_call=True
)
def update_markers(n_clicks, input_value, input_dist):
    if(n_clicks):
        if len(input_value) < 7:
            result = "Enter at least 6 characters"
            return(result)

        query = base_url + api_key + "&text=" + input_value + "&boundary.country=NZ"

        call = requests.get(query, headers=headers)
        data = call.json()

        address = data['features'][0]['properties']['name']
        lat = data['features'][0]['geometry']['coordinates'][1]
        lng = data['features'][0]['geometry']['coordinates'][0]
    
        total_places = 0
        U2_places = 0
        all_meshblocks = []

        markers = [dl.Marker(id={'type': 'marker', 'index': address}, position=[lat, lng], title=str(address))]

        for item, row in services.iterrows():
            
            s_lat = row['Latitude']
            s_lng = row['Longitude']

            dist = geopy.distance.geodesic((s_lat, s_lng), (lat, lng)).km

            if(dist < input_dist):
                s_name = row['Service Name']
                s_pop = row['pop']
                s_address = row['Street']
                s_type = row['Service Type']
                s_20 = row['20 Hours ECE']
                s_EQI = row['Equity Index']
                s_max = row['Max. Licenced Positions']
                s_U2 = row['Under 2\'s']

                total_places = total_places + s_max
                U2_places = U2_places + s_U2

                for mesh in ast.literal_eval(row['mesh']):
                    all_meshblocks.append(mesh)


                tool_tip = dl.Tooltip(s_name + ", " + str(s_pop))

                markers.append(dl.Marker(id={'type': 'marker', 'index': s_name, 'population': s_pop, 'address': s_address, 'type' : s_type, '20hrs' : s_20, 'EQI': s_EQI, 'max_positions': s_max, 'under_2': s_U2, 'over_2': s_max - s_U2, 'dist': dist}, position=[s_lat, s_lng], children=tool_tip))
            

            #filter to unique meshblocks only
            all_meshblocks_filtered = list({v['mesh_id']:v for v in all_meshblocks}.values())

            #demand results
            demand = {'total_pop': 0, 'U5_pop': 0, 'ECE_pop': 0,'total_places': 0, 'status': ''}

            demand['total_pop'] = sum(item['pop'] for item in all_meshblocks_filtered if item['pop'] > 0)
            demand['U5_pop'] = round(demand['total_pop'] * prop_U5, 0)
            demand['ECE_pop'] = round(demand['U5_pop'] * prop_att, 0)
            demand['total_places'] = total_places
            if(demand['total_places'] < demand['ECE_pop']):
                demand['status'] = 'over'
            else:
                demand['status'] = 'under'

            # sort markers
            home = markers[0]
            markers.pop(0)
            markers = sorted(markers, key=lambda d: d.id['dist'])
            markers.insert(0, home)

        return (markers, demand)
    else:
        markers = []
        demand = {}
        return (markers, demand)

#update map
@app.callback(
        [Output('map', 'children'),
         Output('search-results', 'children', allow_duplicate=True),
         Output('results-card', 'children')],
        [Input('markers', 'data'),
         Input('clicked_marker', 'data'),
         Input('demand', 'data')],
         [State(component_id='distance-slider', component_property='value'),
          State(component_id='polygons', component_property='data')],
         prevent_initial_call=True)
def update_map(markers, clicked_marker, demand,input_dist, polygons_list):

    lat = -41.87057
    lng = 173.29466

    zoom = 6

    results_card = ''

    polygons = []

    #no markers exist
    if(markers is None):
        markers = []


    #markers have been created to display on the map
    if(len(markers) > 0):
        source = markers[0]['props']['position']

        lat = source[0]
        lng = source[1]
        zoom = 13

        result_text =  "Your search returned " + str(len(markers) - 1) + " ECE service(s) within " + str(input_dist) + " km."

        results_card = html.Div(
            dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(result_text),
                                html.Br(),
                                html.Div('Total places available: ' + str(demand['total_places'])),
                                html.Br(),
                                html.Div('Estimated ECE pop: ' + str(demand['ECE_pop'])),
                                html.Br(),
                                html.Div('This area is ' + demand['status'] + ' demand.')
                            ]
                            )
                    ]
                    )
        )
    
    #markers have been created to display on the map
    if(len(markers) > 0 and clicked_marker['service_name'] != ''):

        source = markers[0]['props']
        destination = clicked_marker

        s_lat = source['position'][0]
        s_lng = source['position'][1]


        source = str(s_lng) + "," + str(s_lat)
        destination = str(clicked_marker['lng']) + ',' + str(clicked_marker['lat'])


        route = get_directions(source, destination)

        polyline = dl.Polyline(positions=route)

        zoom = 13
        lat = s_lat
        lng = s_lng

    cards = []
    for service in enumerate(markers[1:]):
        s_name = service[1]['props']['id']['index']
        s_type = service[1]['props']['id']['type']
        s_pop = service[1]['props']['id']['population']
        s_address = service[1]['props']['id']['address']
        s_EQI = service[1]['props']['id']['EQI']
        s_20 = service[1]['props']['id']['20hrs']
        s_max = service[1]['props']['id']['max_positions']
        s_u2 = service[1]['props']['id']['under_2']
        s_o2 = service[1]['props']['id']['over_2']
        s_dist = round(service[1]['props']['id']['dist'],2)

        card = html.Div(
                dbc.Card(
                    dbc.CardBody(
                        children=[ 
                            html.H6(s_name, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '700'}),
                            html.P(s_type, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'black', 'font-weight': '300'}),
                            html.P(s_address, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(120, 139, 148)', 'font-weight': '300'}),
                            html.P(str(s_dist) + " km away", style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(120, 139, 148)', 'font-weight': '300'}),
                            dbc.Accordion(
                                dbc.AccordionItem([
                                    html.P("Approved child places: " + str(s_max), id='approved-places', style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    dbc.Tooltip("The amount of child places that the service is approved for.", target='approved-places'),
                                    html.P("Under 2 places: " + str(s_u2), style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    html.P("Over 2 places: " + str(s_o2), style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    html.P("20 Hours Free: " + s_20, style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    html.P(str(s_EQI), style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'}),
                                    html.P("Estimated population serviced: " + str(s_pop), style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '300'})
                                ],
                                title="Show details",
                                style={'padding': '0px'}),
                                start_collapsed=True
                            )
                        ]
                    )
                    ), style={'margin': '20px'}
                )
        cards.append(card)

    return (dl.Map(children = 
                   [dl.TileLayer(), 
                    geojson,
                    markers_geojson], 
                    center = (lat, lng),
                    zoom = zoom,
                    style={'width': '100%', 'height': '100vh', 'margin': "auto", "display": "block"}), cards, results_card)

#marker is clicked
@app.callback(
    [Output("address-card", 'children'),
    Output('search-results', 'children'),
    Output("marker_clicked", "children"),
    Output('clicked_marker', 'data'),
    Output("offcanvas", "is_open"),
    Output("service-name", "children"),
    Output('pop','children')],
    [Input({'type': 'marker', 'index': ALL}, 'n_clicks'),
    Input('markers', 'data')],
    [State("offcanvas", "is_open"),
     State(component_id='address_input', component_property="value")]
)
def marker_click(*args):

    if not any(list(args[0])):
        clicked_marker = {'service_name' : "", 'lat' : "", 'lng' : "", 'dist' : ""}
        return (None, None, "", clicked_marker, True, "", "")

    search_address = args[3]

    service_name = json.loads(dash.callback_context.triggered[0]['prop_id'].split(".")[0])["index"]

    for idx, item in enumerate(args[1]):
        if(item['props']['id']['index'] == service_name):
            
            a_lat = args[1][0]['props']['position'][0]
            a_lng = args[1][0]['props']['position'][1]

            s_lat = item['props']['position'][0]
            s_lng = item['props']['position'][1]

            dist = geopy.distance.geodesic([item['props']['position']], [args[1][0]['props']['position']]).km

            pop = services.loc[services['Service Name'] == service_name]['pop'].values[0]

    
    clicked_marker = {'service_name' : service_name, 'lat' : s_lat, 'lng' : s_lng, 'dist' : dist}

    #no service selected so prompt user to select a service
    if (service_name == search_address):
        service_name = "Click on a marker to view service information"
        dist = ""


    is_open = True

    card = dbc.Card(
        dbc.CardBody(
            children=[html.H5("Search address", className='card-title'),
                        html.P(search_address)]        
        )
    )

    cards = []
    for idx, service in enumerate(args[1][1:]):
        card = dbc.Card(
            children=[ html.P(service['props']['id']['index']),
                       html.P("population")
                     ]
                )
        cards.append(card)
    

    return (
        card,
        cards,
        "{}, is located about {} km from {}".format(service_name, dist, search_address), 
        clicked_marker, 
        is_open, 
        "You have selected service: " + service_name,
        "{} has approximately {} people living within 10km".format(service_name, pop))

#polygon clicked
@app.callback(
    [Output('results-card', 'children', allow_duplicate=True),
     Output('search-results', 'children', allow_duplicate=True)],
    Input('locales', 'n_clicks'),
    State('locales', 'clickData'),
    prevent_initial_call=True
)
def poly_click(n_clicks, feature):

    results_card = ''
    cards = []

    if (feature is not None):
        print(feature['properties'])

        services = feature['properties']['ece_services']

        total_places = 0
        total_services = 0

        for service in services:
            card = create_result_card(service['name'], service['lat'], service['lng'], service['type'], service['max'], service['20_free'], service['U2s'])


            total_places = total_places + service['max']
            total_services = total_services + 1
            cards.append(card)

        results_card = html.Div(
            dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(feature['properties']['name'], style={'font-family': 'Nunito, sans-serif', 'font-size': '15px', 'color': 'rgb(35, 22, 115)', 'font-weight': '700'}),
                                html.Br(),
                                html.Div('Total Early Learning centres: ' + str(total_services)),
                                html.Div('Total places available: ' + str(total_places)),
                                html.Br(),
                                html.Div('Estimated ECE pop: ' + str('ece pop')),
                                html.Br(),
                                html.Div('ECE demand: ' + str(feature['properties']['ece_capacity']))
                            ]
                            )
                    ]
                    )
        )

    return(results_card, cards)


#run app
if __name__ == '__main__':
    app.run(debug=True)