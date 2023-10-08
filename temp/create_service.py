import pandas as pd
import os
import geopandas as gpd
import geopy.distance
from shapely.geometry import Point

#create relative filepaths
dir_path = os.path.abspath('')
pop_data_path = os.path.join(dir_path, 'data\\population.csv')
ece_services_data_path = os.path.join(dir_path, 'data\\ece_services.csv')
meshblock_data_path = os.path.join(dir_path, 'data\\meshblock.csv')

print("loading data")

#load datasets
pop_df = pd.read_csv(pop_data_path)
ece_services_df = pd.read_csv(ece_services_data_path)
meshblock_df = pd.read_csv(meshblock_data_path)

print("data loaded")

#drop services with bad latitude or longitude data
ece_services_df = ece_services_df.drop(ece_services_df[ece_services_df['Latitude'] > 90].index)
ece_services_df = ece_services_df[ece_services_df['Latitude'].notna()]
ece_services_df = ece_services_df[ece_services_df['Longitude'].notna()]

#filter ece services to just columns needed
ece_services_df = ece_services_df[['Service Name', 'Latitude', 'Longitude', 'Town / City', 'General Electorate', 'Street', 'Suburb', 'Town / City', 'Territorial Authority', 'Service Type', '20 Hours ECE', 'Equity Index', 'Max. Licenced Positions', 'Under 2\'s']]

#tidy up Auckland ta
ece_services_df['Territorial Authority'].replace(['Auckland.*'], 'Auckland', regex=True, inplace=True)

#join meshblock and population by meshblock data
meshblock_df.rename(columns={'MB2020_V1_00' : 'MB_ID'}, inplace=True)
pop_df.rename(columns={'MB2020_V2_00' : 'MB_ID'}, inplace=True)

pop_meshblock_df = pd.merge(meshblock_df, pop_df, how='left', on='MB_ID')
pop_meshblock_df = pop_meshblock_df[['MB_ID', 'LATITUDE', 'LONGITUDE', 'General_Electoral_Population', 'GED2020_V1_00_NAME', 'GED2020_V1_00_NAME_ASCII']]
pop_meshblock_df.rename(columns={'GED2020_V1_00_NAME_ASCII' : 'General Electorate'}, inplace=True)

#create dev versions of data
ece_services_df_dev = ece_services_df

#creates a dictionary that has the distance between a service and every meshblocks within the provided electorate
def calculate_distance(s_lat, s_lon, electorate):
    result = []

    electorate_meshblocks_df = pop_meshblock_df[pop_meshblock_df['General Electorate'] == electorate]

    for item, row in electorate_meshblocks_df.iterrows():
        
        mesh_id = row['MB_ID']
        m_lat = row['LATITUDE']
        m_lon = row['LONGITUDE']
        pop = row['General_Electoral_Population']

        dist = geopy.distance.geodesic((s_lat, s_lon), (m_lat, m_lon)).km

        entry = {'mesh_id' : mesh_id, 'lat' : m_lat, 'lon' : m_lon, 'dist' : dist, 'pop' : pop}

        result.append(entry)

    return result

print("creating meshblock distance dictionary for each service")

#create meshblock dictionary for each ece service
#the meshblock dictionary has the distance between each service and each meshblock in that service's region
ece_services_df_dev["mesh"] = ece_services_df_dev.apply(lambda row: calculate_distance(row['Latitude'], row['Longitude'], row['General Electorate']), axis =1)

print("meshblock dictionaries created")

#filter meshblock dictionary to only those meshblocks within 10 kms
def close_mesh(mesh_list):
    result = []

    for idx, item in enumerate(mesh_list):
        if(item['dist'] < 10):
            result.append(item)
    
    return(result)

#calculate the total population for all meshblocks in the mesh_list provided
def pop_near(mesh_list):
    result = 0

    for idx, item in enumerate(mesh_list):
        if (item['pop'] != -999):
            result = result + item['pop'] 
    
    return(result)

print("filtering meshblock dictionaries")

#filter mesh list for each service to only close meshs
ece_services_df_dev['mesh'] = ece_services_df_dev.apply(lambda row: close_mesh(row['mesh']), axis =1)

print("meshblock filtering complete")

print("summing population")

#sum population near 
ece_services_df_dev['pop'] = ece_services_df_dev.apply(lambda row: pop_near(row['mesh']), axis =1)

print("summing population complete")

#create tooltip
ece_services_df_dev['tooltip'] = ece_services_df_dev['Service Name']

#TODO: Check for duiplicate columns in the df, this is causing the creationg of geoJSON to fail

print(ece_services_df_dev.columns)

#save data to df
ece_services_df_dev.to_csv('data\\ece_services_pop.csv', encoding='utf-8')

print("updated services df saved")

print("creating GeoJSON representation")

#create a GeoDataFrame from the DataFrame
ece_services_df_dev['geometry'] = ece_services_df_dev.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)

gdf = gpd.GeoDataFrame(ece_services_df_dev, geometry='geometry')

gdf.drop(['Unnamed: 0', 'Town / City.1'], inplace=True, axis=1)

#create GeoJSON
gdf.to_file('services.geojson', driver='GeoJSON')
