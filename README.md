# Weather Planning Tool

## Overview 

This tool is intended for planning roadtrips spanning several months travelling across different climate zones.
The main goal is to provide additional information on the weather conditions to be expected on the trip to facilitate planning regarding equipment, clothing etc.

There are two main components: The weather eploration component and the time-planning component.

The weather exploration component allows the user to specify a certain month and target, such as average temperature or pecipitation, based on which a map is generated displaying the selected target for each stop on the route.
Clicking on a specific city on the map will provide a city-specific deep-dive, showing the historical temperature (minimum, avgerage and maximum) and precipitation for the full year.

The time-planning component automatically designs the route according to the shortest distance between the cities, starting from a starting point selected by the user. The tool provides a table showing the aerial distance between cities as a rough (!) estimation of the driving distance from one stop to the next. Based upon this distance estimation, the user can then input the estimated time needed to travel from one city to the next. This should include potential overnight stays in between. Upon finalizing this input, the final route will be displayed providing additional information per stop, such as estimated date of arrival (based on user selected starting date) and estimated weather on the date of arrival (based on historical weather data). The tool will additionally display the weather along the route in a final map.

![Alt text](screens/screen_full.png?raw=true "Full Screenshot")


## Functionality

The base route provided follows the Panamerican Highway from Alaska, USA, to Tierra del Fuego, Argentina.
Cities can be added and removed in the Streamlit tool, the respective weather data will automatically be added if the respective geodata has been downloaded into the Geodata folder.

![Alt text](screens/screen_1_add_remove_city.png?raw=true "Adding and removing cities")

Currently supported countries are: Argentina, Canada, Chile, Colombia, Costa Rica, Ecuador, El Salvador, 
Guatemala, Mexico, Nicaragua, Panama, Peru, USA and Uruguay.
The historical weather data is collected via the Meteostat API. Where available, Meteostat's normals from 1991-2020 are used. In cases with missing normals, they are substituted by daily averages from 1991 to 2020.

## File Structure

- /screens/: Screenshots of Streamlit application
- requirements.txt: Python package requirements
- main.py: Main Python file containing streamlit app
- data_utils.py: Data loading and preprocessing
- weather_utils.py: Adding historical weather data
- plotting_utils.py: Generating mapsand plots for tool 
- cities.pickle: Dictionary containing lists of cities on route per country
- To be created locally: /Geodata/ < country > .csv: CSV mapping cities to their geo-coordinates


## Setup Guide
    
- Clone this repository
- Create new conda environment
- Install all packages from the requirements.txt file
- Activate the new environment
- Navigate to the local copy of the repository
- Create a folder "Geodata"
- Go to simplemaps.com and download the geodata for all relevant countries. The files should be named < country >.csv, e.g. Chile.csv.
- Run "streamlit run main.py"


## Data Sources

- GPS database is sourced from SimpleMaps: 
    - USA: https://simplemaps.com/data/us-cities. 
    - Canada: https://simplemaps.com/data/canada-cities.
    - Mexico, Guatemala, El Salvador, Nicaragua, Costa Rica, Panama, Colombia, Ecuador, Peru, Chile, Argentina, Uruguay: Covered under MIT license
- Weather data is sourced from Meteostat: https://meteostat.net
