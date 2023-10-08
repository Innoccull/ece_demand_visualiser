#script to create an ece demand summary for each locality in New Zealand
#an ece deman summary includes the locality population, ece services within it, ece places within it and an estimate of how well ece demand is being met

import pandas as pd
from shapely.geometry import Point, Polygon
from shapely import wkt
from shapely.ops import transform

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

#filter locale columns to just what is needed
locales_df = locales_df[['WKT', 'name', 'type', 'population_estimate', 'territorial_authority_ascii']]

#rename ta column
locales_df.rename(columns={'territorial_authority_ascii' : 'ta'}, inplace=True)

#tidy up territorial authorities
ece_services_df['Territorial Authority'].replace(['Auckland.*'], 'Auckland', regex=True, inplace=True)

#filter out locales that do not realte to places where people might live
locales_df = locales_df.loc[locales_df['type'] != 'Coastal Bay']
locales_df = locales_df.loc[locales_df['type'] != 'Lake']
locales_df = locales_df.loc[locales_df['type'] != 'Inland Bay']

#function to calculate the ece capacity for a given locale
#inputs are a locale population, the ta for the locale and the polygon for the locale
#output: json object with population, ece demand and service details for the locale
def ece_capacity(locale_pop, locale_ta, locale_poly):
    ece_capacity = 0
    ece_services = []

    #population as NaN is set to 0 population
    if (pd.isna(locale_pop)):
        locale_pop = 0

    #get services just for this ta - reduces down the services that need to be iterated
    ece_services_ta_df = ece_services_df[ece_services_df.apply(lambda x: x['Territorial Authority'] in locale_ta, axis=1)]

    #get the Polygon for the locale
    polygon = wkt.loads(locale_poly)

    #iterate through services in the tas covered by the locale
    for item, row in ece_services_ta_df.iterrows():

        #crete a point for the location of the service
        point = Point(row['Longitude'], row['Latitude'])

        #check if service is within the locale
        if (point.within(polygon)):

            #add service's ca[acity to the max licensed positions
            ece_capacity = ece_capacity + row['Max. Licenced Positions']

            #get the details for the service and add to the list of services
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
                
    prop_U5 = 0.059
    prop_att = 0.607

    #calculate ece relevant population for the locale
    U5_pop = round(locale_pop * prop_U5, 2)
    ece_pop = round(U5_pop * prop_att, 2)

    #locale population is 0 - set demand to -1 to indicate it is not relevant for that locale
    if (locale_pop == 0):
        ece_demand = -1
    else:
        #calculate ece_capacity - if there is no capacity but there is population demand, set to 99
        if(ece_capacity == 0 and locale_pop > 0):
            ece_demand = 99
        else:
            ece_demand = round(ece_pop/ece_capacity, 2)

    result = {
        'total_pop' : locale_pop,
        'U5_pop' : U5_pop,
        'ece_pop' : ece_pop,
        'ece_places' : ece_capacity,
        'ece_services' : ece_services,
        'ece_capacity' : ece_demand        
    }
            
    #returns the overall capacity and list of services in that locale
    return(result)

print("calculating ece capacity and demand")

#calculate ece capacity for each locale - this is the total ece places available
locales_df["ece_capacity"] = locales_df.apply(lambda row: ece_capacity(row['population_estimate'], row['ta'],row['WKT']), axis =1)

print("saving ece demand to csv")

locales_df.to_csv('data\\ece_demand.csv', encoding='utf-8')

print("ece demand calculated and saved")