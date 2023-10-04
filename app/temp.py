dl.Map(children = [
            dl.TileLayer(), 
            markers_gj, 
            locales,
            colorbar],
           id="map", 
           center = (lat, lng),
           style={'width' : '100%', 'height' : '100vh', 'margin' : 'auto', 'display' : 'block'}
        )


_____________

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

_____________________

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
    
    ____________

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

____________________________


