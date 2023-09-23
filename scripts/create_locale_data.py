import pandas as pd
import shapely
from shapely.geometry import Point, Polygon
from shapely import wkt
import geopandas as gpd


print("loading data")

#import necessary data
locales_df = pd.read_csv("data\\nz_suburbs_and_localities.csv")
ece_services_df = pd.read_csv("data\\ece_services.csv")

#drop services with bad latitude or longitude data
ece_services_df = ece_services_df.drop(ece_services_df[ece_services_df['Latitude'] > 90].index)
ece_services_df = ece_services_df[ece_services_df['Latitude'].notna()]
ece_services_df = ece_services_df[ece_services_df['Longitude'].notna()]

#filter ece services to just columns needed
ece_services_df = ece_services_df[['Service Name', 'Latitude', 'Longitude', 'Town / City', 'General Electorate', 'Street', 'Suburb', 'Town / City', 'Territorial Authority', 'Service Type', '20 Hours ECE', 'Equity Index', 'Max. Licenced Positions', 'Under 2\'s']]

#tidy up territorial authorities
ece_services_df['Territorial Authority'].replace(['Auckland.*'], 'Auckland', regex=True, inplace=True)


#function to calculate the ece capacity for a given locale
def ece_capacity(locale_pop, locale_ta, locale_poly):
    ece_capacity = 0
    ece_services = []

    if (pd.isna(locale_pop)):
        return(0)
    else:

        #get services just for this ta
        ece_services_ta_df = ece_services_df[ece_services_df.apply(lambda x: x['Territorial Authority'] in locale_ta, axis=1)]

        #get the Polygon for the ta
        polygon = wkt.loads(locale_poly)

        # if (len(ece_services_ta_df) == 0):
        #     print(locale_ta + " returned " + str(len(ece_services_ta_df)) + " services.")

        #iterate through services in the tas covered by the locale
        for item, row in ece_services_ta_df.iterrows():

            #crete a point for the location of the service
            point = Point(row['Longitude'], row['Latitude'])

            #check if service is within the locale
            if (point.within(polygon)):

                #get the details for the service and add to the list of services
                ece_capacity = ece_capacity + row['Max. Licenced Positions']
                ece_services.append(
                    {'name': row['Service Name'], 
                     'lat' : row['Latitude'], 
                     'lng' : row['Longitude'], 
                     'max' : row['Max. Licenced Positions'],
                     'type': row['Service Type'],
                     '20_free' : row['20 Hours ECE'],
                     'U2s' : row['Under 2\'s']
                     }
                     )

        return([ece_capacity, ece_services])


#function to calculate the ece demand for a locale
def ece_demand(population, ece_profile):
    prop_U5 = 0.059
    prop_att = 0.607
    
    #there is no population in this locale so no demand
    if (pd.isna(population)):
        return(0)
    else:

        U5_pop = round(population * prop_U5)
        ece_pop = round(U5_pop * prop_att)

        if (ece_profile[0] == 0):
            ece_capacity = 0
        else:
            ece_capacity = round(ece_pop/ece_profile[0], 2)

        result = {
            'total_pop' : population,
            'U5_pop' : U5_pop,
            'ece_pop' : ece_pop,
            'ece_places' : ece_profile[0],
            'ece_services' : ece_profile[1],
            'ece_capacity' : ece_capacity        
        }

    return (result)

#function to get the coordinates for a WKT polygon
def get_poly_coordinates(poly):

    #create geometry view
    polygon =  wkt.loads(poly)
    polygon = shapely.geometry.mapping(polygon)

    positions = polygon['coordinates']
    positions = [list(elem) for elem in list(positions[0])]

    for item in positions:
        item.reverse()

    return (positions)

#identifies if the ta is covered by the locale
def identify_ta(locale_ta, target_tas):
    
    for ta in target_tas:
        if ta in locale_ta:
            return (True)
    
    return (False)

print("calculating ece capacity and demand")

#calculate ece capacity for each locale
locales_df["ece_capacity"] = locales_df.apply(lambda row: ece_capacity(row['population_estimate'], row['territorial_authority_ascii'],row['WKT']), axis =1)

#calculate ece demand for each locale
locales_df["ece_demand"] = locales_df.apply(lambda row: ece_demand(row['population_estimate'], row['ece_capacity']), axis =1)

#identify which locales are within Christchurch City TA
locales_df['include'] = locales_df.apply(lambda row: identify_ta(row['territorial_authority_ascii'], ['Christchurch City', 'Selwyn District', 'Waimakariri']), axis=1)

#tidy up locales_df into analysis format
locales_df.drop(['ece_capacity'], inplace=True, axis=1)
locales_df = pd.concat([locales_df.drop('ece_demand', axis=1),  pd.json_normalize(locales_df['ece_demand'])], axis=1)
locales_df = locales_df[['WKT', 'id', 'name', 'total_pop', 'U5_pop', 'ece_pop', 'ece_places', 'ece_services', 'ece_capacity', 'include']]
locales_df['geometry'] = locales_df['WKT'].apply(lambda x: shapely.wkt.loads(x))

#create coordinates column
locales_df['positions'] = locales_df.apply(lambda row: get_poly_coordinates(row['WKT']), axis =1)

print("saving to csv")

#save ece demand df
locales_df.to_csv('data\\ece_demand.csv', encoding='utf-8')


geojson_df = pd.read_csv("data\\ece_demand.csv")

print("converting to geojson")

#convert to geojson
geojson_df['geometry'] = gpd.GeoSeries.from_wkt(locales_df['WKT'])

geojson_df = geojson_df[locales_df['include'] == True]
geojson_df = geojson_df[['name', 'ece_services', 'ece_capacity', 'total_pop', 'U5_pop', 'ece_pop', 'geometry']]

gdf = gpd.GeoDataFrame(geojson_df, geometry='geometry')
gdf = gdf[['name', 'ece_services', 'total_pop', 'U5_pop', 'ece_pop', 'ece_capacity', 'geometry']]

# Save the GeoDataFrame to a GeoJSON file (replace 'output.geojson' with your desired file path)
gdf.to_file('locales.geojson', driver='GeoJSON')

print("GeoJSON file saved successfully.")