import pandas as pd
import shapely
from shapely.geometry import Point, Polygon
from shapely import wkt
import geopandas as gpd
import pyproj
from shapely.ops import transform
import ast


print("loading data")

#import necessary data
locales_demand_df = pd.read_csv("data\\ece_demand.csv")


#function to convert the coordinates for a polygon object
#input: WKT polygon object
#output: 
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

#convert coordinates for polygon
def convert_coordinates(nztm_poly):

    nztm_poly = wkt.loads(nztm_poly)

    nztm = pyproj.CRS('EPSG:2193')
    nzgd2000 = pyproj.CRS('EPSG:4167')
    
    project = pyproj.Transformer.from_crs(nztm, nzgd2000, always_xy=True).transform
    nzgd2000_poly = transform(project, nztm_poly)

    return (nzgd2000_poly)

#get regions that this locale is a part of
def get_ta(poly):
    ta = ''
    polygon = wkt.loads(poly)

    for item, row in ta_df.iterrows():
        region_poly = row['WKT_U']

        if polygon.intersects(region_poly):
            ta = row['TA2022_V1_00_NAME_ASCII']
            
            return ta
        
    return ta

#create dictionary string as dictionary
locales_demand_df['ece_capacity'] = locales_demand_df['ece_capacity'].apply(lambda x: ast.literal_eval(x))

#expand dictionary entries to columns
locales_demand_df = pd.concat([locales_demand_df.drop('ece_capacity', axis=1),  pd.json_normalize(locales_demand_df['ece_capacity'])], axis=1)

#get just one ta for each locale
locales_demand_df['ta'] = locales_demand_df['ta'].apply(lambda x: x.split(',')[0])

#get just the columns needed
locales_demand_df = locales_demand_df[['WKT', 'name', 'total_pop', 'U5_pop', 'ece_pop', 'ece_places', 'ece_services', 'ece_capacity', 'ta']]

#store ece service list as a string so it can be saved to geojson
locales_demand_df['ece_services'] = locales_demand_df['ece_services'].apply(lambda x: str(x))

#convert WKT to a geometry
#locales_demand_df['geometry'] = locales_demand_df['WKT'].apply(lambda x: shapely.wkt.loads(x))

#get just the coordinates in the right format
#locales_demand_df['positions'] = locales_demand_df.apply(lambda row: get_poly_coordinates(row['WKT']), axis =1)

print("converting to geojson")

#convert to geojson
locales_demand_df['geometry'] = gpd.GeoSeries.from_wkt(locales_demand_df['WKT'])

#geojson_df = geojson_df[locales_df['include'] == True]
#geojson_df = locales_demand_df[['name', 'ece_services', 'ece_capacity', 'total_pop', 'U5_pop', 'ece_pop', 'territorial_authority_ascii', 'geometry']]

gdf = gpd.GeoDataFrame(locales_demand_df, geometry='geometry')
gdf = gdf[['name', 'total_pop', 'U5_pop', 'ece_pop', 'ece_capacity', 'ece_services', 'ta', 'geometry']]

# Save the GeoDataFrame to a GeoJSON file (replace 'output.geojson' with your desired file path)
gdf.to_file('locales.geojson', driver='GeoJSON')

print("GeoJSON file saved successfully.")