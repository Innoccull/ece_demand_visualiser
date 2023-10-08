import pandas as pd
import os
import geopandas as gpd
import geopy.distance
from shapely.geometry import Point

#create relative filepaths
dir_path = os.path.abspath('')
pop_data_path = os.path.join(dir_path, 'data\\population.csv')
ece_services_data_path = os.path.join(dir_path, 'data\\ece_services.csv')

print("loading data")

#load datasets
ece_services_df = pd.read_csv(ece_services_data_path)

print("data loaded")

#drop services with bad latitude or longitude data
ece_services_df = ece_services_df.drop(ece_services_df[ece_services_df['Latitude'] > 90].index)
ece_services_df = ece_services_df[ece_services_df['Latitude'].notna()]
ece_services_df = ece_services_df[ece_services_df['Longitude'].notna()]

#filter ece services to just columns needed
ece_services_df = ece_services_df[['Service Name', 'Latitude', 'Longitude', 'Territorial Authority', 'Service Type', '20 Hours ECE', 'Max. Licenced Positions', 'Under 2\'s']]

#tidy up Auckland ta
ece_services_df['Territorial Authority'].replace(['Auckland.*'], 'Auckland', regex=True, inplace=True)

#create tooltip
ece_services_df['tooltip'] = ece_services_df['Service Name']


print("creating GeoJSON representation")

#create a GeoDataFrame from the DataFrame
ece_services_df['geometry'] = ece_services_df.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)

gdf = gpd.GeoDataFrame(ece_services_df, geometry='geometry')

print(gdf.columns)

#create GeoJSON
gdf.to_file('services.geojson', driver='GeoJSON')
