# ECE Demand Visualiser

The early childhood education (ECE) demand visualiser joins together data from the Ministry of Education (MoE) and Land Information New Zealand (LINZ) into an interactive visualisation that shows whether demand for ECE services in New Zealand is being met. 

The application presents two views of ECE demand in New Zealand: national and locality.

### National View

The national view shows the overall demand for ECE services in New Zealand based on the estimated ECE population and the number of ECE places available in early learning services in New Zealand.


![image info](/app_images/start.png)

The national view also breaks down ece demand by New Zealand Terrirotial Authority (TA) to allow for more localised exploration. The user can select a TA from the table on the left to show that TA on the map and present a summary of ece demand for that TA in the top right. 

![image info](/app_images/ta_selected.png)

### Locality View

The 'locality view' shows the details for specific localities within a territorial authority. Each territorial authority is broken down into localities that are obtained from Land Information New Zealand (LINZ).

![image info](/app_images/ta_selected.png)

Localities will be shaded according to ece demand:
- Red means a locality is over-demand
- Orange means a locality is near-demand
- Green means a locality is under-demand
- Grey means there is no population in that locality

<video src="app_images/test_vid.mp4" controls title="Title"></video>

The user can choose to display markers for services within a locality.

Clicking on a locality on the map will show details for that locality. This detail includes a summary of ece demand for that locality (total early learning centres, total places available, estimated ece population and ece demand) and a list of early learning services.

![image info](/app_images/locality_selected_2.png)


## ECE demand 

ECE demand is a measure of how well demand for early learning services is being met within a specific location. It is calculated with the following equation: 

> ece population / ece capacity

ECE population is estimated based on information from Land Information New Zealand (LINZ), Statistics New Zealand (SNZ) and the Ministry of Education (MoE). LINZ provides an estimate of population within each locality, SNZ provides an estimate of the proportion of the population that is under 5 and the MoE proides an estimate of the proportion of children attend ECE services. This results in the equation below:

> (locality population * proportion under 5) * proportion attending ece


ECE capcity is obtained by summing up the ECE places that are available for each service. This information is available in the ece service data published by MoE. 


## Technical Details

The ECE Demand Visualiser is built using dash leaflet, a library that supports visualising information on maps.

Early Learning service data was obtained from the MoE ECE directory (https://www.educationcounts.govt.nz/directories/early-childhood-services). This data includes information on early learning service places available and location (in the form of latitutude and longitude). The python script [create_service_data_geojson.py](scripts\create_service_data_geojson.py) creates a geoJSON representation for all early learning services based on the ECE directory data. 

Locality and population data was sourced from LINZ suburbs and localities data(https://data.linz.govt.nz/layer/113764-nz-suburbs-and-localities/). The locality data provided by LINZ includes polygon information which enables visualisation of the locality on a map and an estimted population for each locality. 

The python script [create_locale_demand_csv.py](scripts\create_locale_demand_csv.py) calculates the ece demand for every locality (there are TBD localities) and saves this to a csv file. The python script [create_locale_demand_geojson.py](scripts\create_locale_demand_geojson.py) processes the csv based data into a geoJSON format that can be visualised in dash leaflet.

The locality data is used to visualised locality based information on ece demand and is also summarised up to create ece demand data for each territorial authority. The python script [create_ta_summary_csv.py](scripts\create_ta_summary_csv.py) loads the locality level ece demand detail and summarises ece demand for each territorial authority. 