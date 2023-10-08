import json

with open('locales.geojson') as fp:
    data = json.load(fp)

tas = [
 'Area outside Territorial Authority',
 'Ashburton District',
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
 'Kawerau District',
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

#create a dictionary where each key is a ta and each value is a dictionary that contains stats for the specific ta
result = {k: {
    'total_ece_pop' : 0,
    'total_ece_places' : 0,
    'overall_ece_demand' : 0,
    'total_locales' : 0,
    'over_demand_locales' : 0,
    'near_demand_locales': 0,
    'under_demand_locales' : 0,
    'no_population_locales' : 0,
    'total_services' : 0,
    'lat' : 0,
    'lng' : 0
} for k in tas}

for locale in data['features']:
    ta = locale['properties']['ta']

    result[ta]['total_ece_pop'] = result[ta]['total_ece_pop'] + locale['properties']['ece_pop']

    places = 0

    #check if there are services in the specific locale
    if (len(locale['properties']['ece_services']) != 0):
        
        #get the list of services for the locale
        services = locale['properties']['ece_services']

        #the the total services for the locale to the overall total for the ta
        result[ta]['total_services'] = result[ta]['total_services'] + len(services)
 
        #iterate through serives and add to the total number of places for the locale
        for service in services:
            places = places + service['max']

    #add the total places for the locale to the total places for the ta
    result[ta]['total_ece_places'] = result[ta]['total_ece_places'] + places

    #increment the total localities in the TA by 1
    result[ta]['total_locales'] = result[ta]['total_locales'] + 1

    #increment count of ece demand category
    if (locale['properties']['ece_capacity'] > 1):
        result[ta]['over_demand_locales'] = result[ta]['over_demand_locales'] + 1
    elif (locale['properties']['ece_capacity'] == -1):
        result[ta]['no_population_locales'] = result[ta]['no_population_locales'] + 1
    elif (0.9 <= locale['properties']['ece_capacity'] <= 1):
        result[ta]['near_demand_locales'] = result[ta]['near_demand_locales'] + 1
    else:
        result[ta]['under_demand_locales'] = result[ta]['under_demand_locales'] + 1

for ta in result:
    if(result[ta]['total_ece_places'] != 0):
        result[ta]['overall_ece_demand'] = round(result[ta]['total_ece_pop']/result[ta]['total_ece_places'], 2)
    else:
        result[ta]['overall_ece_demand'] = -1

    result[ta]['total_ece_pop'] = round(result[ta]['total_ece_pop'], 0)

#TODO: create TA centroid

with open('ta_summary.json', 'w') as fp:
    json.dump(result, fp)