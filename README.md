# ECE Demand Visualiser

The early childhood education (ECE) demand visualiser joins together data from the Ministry of Education (MoE) and Land Information New Zealand (LINZ) into an interactive visualisation that shows whether demand for ECE services in New Zealand is being met. 

The application presents two views of ECE demand in New Zealand: national and locality.

### National View

The national view shows the overall demand for ECE services in New Zealand based on the estimated ECE population and the number of ECE places available in early learning services in New Zealand.

![image info](/app_images/national_view.PNG)

The national view also breaks down ece demand by New Zealand Terrirotial Authority (TA) to allow for more localised exploration. The user can select a TA from the table on the left - this will show that TA on the map and generate a summary of ece demand for that TA in the top right. 

![Alt text](app_images/select_ta.gif)

### Locality View

The locality view shows the details for specific localities within a TA. Each TA is broken down into localities that are obtained from Land Information New Zealand (LINZ).

Localities are shaded according to ece demand:
- Red means a locality is over-demand
- Orange means a locality is near-demand
- Green means a locality is meeting demand
- Grey means there is no population in that locality

Clicking on a locality on the map will show details for that locality. This detail includes a summary of ece demand for that locality (total early learning centres, total places available, estimated ece population and ece demand) and a list of early learning services that are within that locality.

![Alt text](app_images/select_locality.gif)

## ECE demand 

ECE demand is a measure of how well demand for early learning services is being met within a specific location. It is calculated according to the following equation: 

> ece demand = ece population / ece capacity

ECE population is estimated based on information from Land Information New Zealand (LINZ), Statistics New Zealand (SNZ) and the Ministry of Education (MoE). LINZ provides an estimate of population within each locality, SNZ provides an estimate of the proportion of the population that is under 5 and the MoE proides an estimate of the proportion of children under 5 that attend ECE services. This results in the equation below:

> ece population = (locality population * proportion under 5) * proportion attending ece


ECE capcity is obtained by summing up the ECE places that are available for each service. This information is available in the ece service data published by MoE. 


## Technical Details

The ECE Demand Visualiser is built using dash leaflet (https://www.dash-leaflet.com/), a library that supports visualising information on interactive maps in plotly dash applications (https://plotly.com/dash/).

Early Learning service data was obtained from the MoE ECE directory (https://www.educationcounts.govt.nz/directories/early-childhood-services). This data includes information on early learning service places available and location (in the form of latitutude and longitude). The python script [create_service_data_geojson.py](scripts\create_service_data_geojson.py) creates a GeoJSON representation for all early learning services based on the ECE directory data. 

Locality and population data was sourced from LINZ suburbs and localities data (https://data.linz.govt.nz/layer/113764-nz-suburbs-and-localities/). The locality data provided by LINZ includes polygon information which enables visualisation of the locality on a map and an estimted population for each locality which allows calculation of ECE population. 

The python script [create_locale_demand_csv.py](scripts\create_locale_demand_csv.py) calculates the ece demand for every locality (there are TBD localities) and saves this to a csv file. The python script [create_locale_demand_geojson.py](scripts\create_locale_demand_geojson.py) processes the csv based data into a GeoJSON format that can be visualised in dash leaflet.