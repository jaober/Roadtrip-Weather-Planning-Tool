"""
Backend functions for data loading and data preprocessing.
"""

import pandas as pd
import os
import pickle
import streamlit as st
from weather_utils import *
import geopy.distance
from datetime import timedelta

GEODATA_PATH = 'Geodata'

os.system('color')

# Load dictionary of cities on route from file
with open('cities.pickle', 'rb') as handle:
    cities = pickle.load(handle)
    
    
class bcolors:
    """ Specifies colors for custom colored error and warning messages. """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    
def add_city(cities, panam_cities, city_normals, country, city):
    """
    Adds a new city to the data.
    
    Args:
        cities (dict): Dictionary of cities on route.
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        country (str): Name of country in which the new city is located.
        city (str): Name of new city to add.
        
    Returns:
        cities (dict): Updated dictionary of cities on route with new city added.
        panam_cities (pandas.DataFrame): Updated dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Updated dictionary containing the retrieved historical weather normals for each city. 
        
    """
    with open('cities.pickle', 'wb') as handle:
        cities[country].append(city)
        pickle.dump(cities, handle, protocol=pickle.HIGHEST_PROTOCOL)
    panam_cities, city_normals = add_info_new_city(panam_cities, city_normals, city, country)
    return cities, panam_cities, city_normals
    
    
def remove_city(cities, panam_cities, city_normals, country, city):
    """
    Removes a city from the data.
    
    Args:
        cities (dict): Dictionary of cities on route.
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        country (str): Name of country in which the city to be removed is located.
        city (str): Name of city to be removed.
        
    Returns:
        cities (dict): Updated dictionary of cities on route with specified city removed.
        panam_cities (pandas.DataFrame): Updated dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Updated dictionary containing the retrieved historical weather normals for each city. 
        
    """
    panam_cities, city_normals = remove_info_old_city(panam_cities, city_normals, city, country)
    with open('cities.pickle', 'wb') as handle:
        cities[country].remove(city)
        pickle.dump(cities, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return cities, panam_cities, city_normals
    
    
def check_geodata(relevant_geodata, cities, country):
    """
    Checks whether all cities of a given country have been successfully matched with their respective geodata. 
    If applicable, prints an error message listing the unmatched cities.
    
    Args:
        relevant_geodata (pandas.DataFrame): Subset of geodata dataframe for which city names match cities on route.
        cities (dict): Dictionary of cities on route.
        country (str): Name of country.
        
    """
    matched_cities = len(relevant_geodata)
    total_cities = len(cities[country])
    if matched_cities != total_cities:
        unmatched_cities = (', ').join([city for city in cities[country] if city not in relevant_geodata.city.values])
        print(f'{bcolors.FAIL}{country} - Cities matched with geodata: {matched_cities}/{total_cities}. Please review the following cities: {unmatched_cities}.{bcolors.ENDC}')
    else:
        print(f'{bcolors.OKGREEN}{country} - Cities matched with geodata: {matched_cities}/{total_cities}.{bcolors.ENDC}')


def add_info_new_city(panam_cities, city_normals, new_city, new_country):
    """
    Adds geodata and normals for new city. Helper function called by add_city.
    
    Args: 
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        new_city (str): Name of new city to add.
        new_country (str): Name of country in which the new city is located.
        
    Returns:
        panam_cities (pandas.DataFrame): Updated dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Updated dictionary containing the retrieved historical weather normals for each city. 
       
    """
    geodata_path = 'Geodata'
    geodata = pd.read_csv(geodata_path+'/'+new_country+'.csv')
    geodata['country'] = new_country
    if new_country == 'United States of America':
        geodata['city'] = geodata['city'] + ',' + geodata['state_id']
    print(geodata.loc[geodata.city == new_city])
    relevant_geodata = geodata.loc[geodata.city == new_city][['country', 'city', 'lat', 'lng']]
    check_geodata(relevant_geodata, {new_country: [new_city]}, new_country)
    city_normals[new_city] = get_normals_per_city(relevant_geodata.iloc[0])
    print(city_normals.keys())
    if len(city_normals[new_city]['Normals']['tavg'].values()) == 0:    
        st.warning(f'No weather data avalable for {new_city} in {new_country}.')
    else:
        panam_cities = pd.concat([panam_cities, relevant_geodata])
    del geodata
    del relevant_geodata
    return panam_cities, city_normals


def remove_info_old_city(panam_cities, city_normals, old_city, old_country):
    """
    Removes weather data and geodata for the city to be removed. Helper function called by remove_city.
    
    Args:
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        old_city (str): Name of city to be removed.
        old_country (str): Name of country in which the city to be removed is located.
        
    Returns:
        panam_cities (pandas.DataFrame): Updated dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Updated dictionary containing the retrieved historical weather normals for each city. 
        
    """
    print(city_normals.keys())
    if old_city in city_normals.keys():
        city_normals.pop(old_city)
    panam_cities = panam_cities.loc[~((panam_cities.city == old_city) & (panam_cities.country == old_country))]
    return panam_cities, city_normals


@st.cache_data
def load_data():
    """
    Main data loading function initializing all relevant dataframes. Adds geo coordinates to each city, as well as historical weather data.
    
    Returns:
        available_cities (dict): Dictionary of cities on route. 
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        st_warnings (list[str]): List of warnings arising during retrieval of historical weather data.
        
    """
    # Load geodata per country
    geodata_path = 'Geodata'
    cities_with_geodata = []
    available_cities = {}
    for filename in os.listdir(geodata_path):
        geodata = pd.read_csv(geodata_path+'/'+filename)
        country = filename.split('.')[0]
        geodata['country'] = country
        if country == 'United States of America':
            geodata['city'] = geodata['city'] + ',' + geodata['state_id']
        relevant_geodata = geodata.loc[geodata.city.isin(cities[country])]
        cities_with_geodata.append(relevant_geodata)       
        check_geodata(relevant_geodata, cities, country)
        available_cities[country] = geodata.city.sort_values().values
        del geodata
        del relevant_geodata
    panam_cities = pd.concat(cities_with_geodata)[['country', 'city', 'lat', 'lng']]
    city_normals = {}
    remove_cities = []
    st_warnings = []
    for i in range(len(panam_cities)):
        city = panam_cities.iloc[i].city
        city_normals[city] = get_normals_per_city(panam_cities.iloc[i])
        if len(city_normals[city]['Normals']['tavg'].values()) == 0:
            normal_substitutes, st_warning = get_normal_substitutes(city, city_normals[city]['Station ID'])
            st_warnings.append(st_warning)
            if len(normal_substitutes) == 1:
                remove_cities.append(panam_cities.iloc[i].city)
            else:
                city_normals[city]['Normals'] = normal_substitutes
    panam_cities = panam_cities.loc[~panam_cities.city.isin(remove_cities)]
    st_warnings = [warning for warning in st_warnings if len(warning) > 0]
    return available_cities, panam_cities, city_normals, st_warnings


def get_lat_lng_dist(x,y):
    """ Returns geodesic distance in kilometers between input coordinate tuples x and y. """
    return geopy.distance.geodesic(x, y).km


def get_route(route_start_date, route_start_city, panam_cities):
    """
    Creates route along cities based on selected starting point by always choosing the closest city as next stop, as measured by the 
    geodesic distance between the cities geo-coordinates.
    
    Args:
        route_start_date (date): Starting date of travel along route.
        route_start_city (str): Name of city to serve as route's starting point.
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        
    Returns:
        route_df (pandas.DataFrame): Contains one row per city, ordered along route, as well as estimated distance and travelling time to
                                     next stop.
        
    """
    # Find closest city
    next_cities = panam_cities.copy()
    next_cities['coords'] = list(zip(next_cities.lat, next_cities.lng))
    route_dict = {0: {'city': route_start_city, 'est_dist': 0, 'days_to_city': 0, 'arrival_date': route_start_date}} 
    current_city = route_start_city
    # Start iteration
    for i in range(len(panam_cities)-1):
        current_coords = next_cities.loc[next_cities.city == current_city].coords
        next_cities = next_cities.loc[next_cities.city != current_city]
        next_cities['est_dist'] = next_cities['coords'].apply(lambda x: get_lat_lng_dist(x, current_coords))
        next_cities = next_cities.sort_values(by='est_dist')
        current_city = next_cities.city.iloc[0]
        est_dist = next_cities.est_dist.iloc[0]
        route_dict[i+1] = {'city': current_city, 'est_dist': 0, 'days_to_city': 0, 
                           'arrival_date': route_dict[i]['arrival_date'] + timedelta(days=route_dict[i]['days_to_city'])}
        route_dict[i]['est_dist'] = str(round(est_dist))+' km'
    del next_cities
    route_df = pd.DataFrame(route_dict).T
    return route_df


def update_route_table(city_normals, route_start_date, route_start_city, panam_cities):
    """
    Updates route table based on user-inputs regarding estimated travelling time between cities with estimated date of arrival at each city.
    Adds historical weather estimates for each city based on estimated date of arrival.
    
    Args:
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        route_start_date (date): Starting date of travel along route.
        route_start_city (str): Name of city to serve as route's starting point.
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        
    Returns:
        route_df (pandas.DataFrame): Contains one row per city, ordered along route, as well as estimated distance and travelling time to
                                     next stop, estimated date of arrival and historical weather estimates for estimated date of arrival.
        
    """
    # Re-initalize route table
    route_df = get_route(route_start_date, route_start_city, panam_cities)
    if 'route_table_edits' in st.session_state:
        # Remove deleted rows
        indices_to_keep = [i for i in range(len(route_df)) if i not in st.session_state['route_table_edits']['deleted_rows']]
        route_df = route_df.iloc[indices_to_keep]
        # Add user inputs
        changes = list(st.session_state['route_table_edits']['edited_cells'].keys())
        if len(changes) > 0:
            for change in changes:
                change_i = int(change.split(':')[0])
                change_j = int(change.split(':')[1])-1
                new_val = st.session_state.route_table_edits['edited_cells'][change]
                route_df.iloc[change_i, change_j] = new_val
        # Calculate estimated arrival date
        for i in range(1, len(route_df)):
             route_df.arrival_date.iloc[i] = route_df.arrival_date.iloc[i-1] + timedelta(days = route_df.days_to_city.iloc[i-1])   
        # Add estimated weather on arrival date
        weather_info = {}       
        for i in range(len(route_df)):
            city = route_df.city.iloc[i]
            arrival_date = route_df.arrival_date.iloc[i]
            arrival_day = arrival_date.day
            arrival_month = arrival_date.month
            arrival_date_pre = arrival_date - timedelta(days = 3)
            arrival_date_post = arrival_date + timedelta(days = 3)
            arrival_day_pre = arrival_date_pre.day
            arrival_month_pre = arrival_date_pre.month
            arrival_day_post = arrival_date_post.day
            arrival_month_post = arrival_date_post.month
            station_id = city_normals[city]['Station ID']
            weather_pre = get_historical_dailies(station_id, arrival_day_pre, arrival_month_pre).round(1).to_dict()
            weather_on = get_historical_dailies(station_id, arrival_day, arrival_month).round(1).to_dict()
            weather_post = get_historical_dailies(station_id, arrival_day_post, arrival_month_post).round(1).to_dict()
            weather_window = {}
            for target in ['tavg', 'tmin', 'tmax', 'prcp', 'snow']:
                weather_window[target] = f'({weather_pre[target]}) {weather_on[target]} ({weather_post[target]})'
            weather_info[city] = weather_window 
        route_df = pd.merge(route_df, pd.DataFrame(weather_info).T.reset_index().rename(columns = {'index':'city'}), 
                            on = 'city', how = 'inner')
        return route_df
