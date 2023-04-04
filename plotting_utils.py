"""
Backend functions generating all plots displayed in the Streamlit application.
"""

import pandas as pd
from matplotlib import pyplot as plt
import geopandas
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
from datetime import timedelta
from data_utils import * 

# Dictionaries mapping backend names of target and month to user-friendly labels for plot titles and labels      
target_dict = {'tavg': 'average temperature (in °C)',
               'tmin': 'minimum temperature (in °C)',
               'tmax': 'maximum temperature (in °C)',
               'prcp': 'precipitation (in mm)'}

month_dict = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
              7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}


def plot_temp_per_city(city_normals, city, month_dict = month_dict):
    """
    Plots minimum, average and maximum temperature for a given city across each month of the year.
    
    Args:
        city_normals (dict): Dictionary mapping all available cities to their respective historical monthly temperatures.
        city (str): Name of the city for which the temperature plot is generated.
        month_dict (dict): Dictionary mapping each month to its full name to make plot more user-friendly to read.
        
    """
    city_weather = pd.DataFrame(city_normals[city]['Normals'])
    timespan = city_normals[city]['Timespan']
    if len(city_weather) == 0:
        print(f'No data available for {city}.')
    else:
        fig, ax = plt.subplots()
        ax.plot(city_weather.index, city_weather.tmax, color = 'orange', label = 'Max')
        ax.plot(city_weather.index, city_weather.tavg, color = 'black', label = 'Avg')
        ax.plot(city_weather.index, city_weather.tmin, color = 'blue', label = 'Min')
        ax.legend()
        ax.set_ylabel('Temperature (°C)')
        ax.set_title(f'Historical Weather in {city} ({timespan})')
        ax.set_xticks(city_weather.index)
        ax.set_xticklabels([month[:3] for month in month_dict.values()], rotation = 45)
        ax.set_ylim(-20, 40)
        st.pyplot(fig)
        
        
def get_max_prcp(city_normals):
    """
    Gets suitable maximum for setting comparable precipitation axis limits via determining the maximum precipitation value across cities.
    
    Args:
        city_normals (dict): Dictionary mapping all available cities to their respective historical monthly temperatures.
        
    Returns:
        max_prcp (float): Maximum precipitation value across cities, increased by 10 to not max out the precipitation axis in plots.
        
    """
    max_prcp = max([max(city_normals[city]['Normals']['prcp'].values()) 
                    for city in city_normals.keys() 
                    if len(city_normals[city]['Normals']['prcp']) > 0])
    max_prcp += 10
    return max_prcp


def plot_rain_per_city(city_normals, city, month_dict = month_dict):
    """
    Plots precipitation for a given city across each month of the year.
    
    Args:
        city_normals (dict): Dictionary mapping all available cities to their respective historical precipitation values.
        city (str): Name of the city for which the temperature plot is generated.
        month_dict (dict): Dictionary mapping each month to its full name to make plot more user-friendly to read.
        
    """
    city_weather = pd.DataFrame(city_normals[city]['Normals'])
    timespan = city_normals[city]['Timespan'] 
    max_prcp = get_max_prcp(city_normals)
    if len(city_weather) == 0:
        print(f'No data available for {city}.')
    else:
        fig, ax = plt.subplots()
        ax.bar(city_weather.index, city_weather.prcp, color = 'blue', label = 'Prcp')
        ax.legend()
        ax.set_ylabel('Mean monthly precipitation total in mm')
        ax.set_title(f'Historical Precipitation in {city} ({timespan})')
        ax.set_xticks(city_weather.index)
        ax.set_xticklabels([month[:3] for month in month_dict.values()], rotation = 45)     
        ax.set_ylim(0, max_prcp)
        st.pyplot(fig)   
    

def expand_dataframe(x, city_normals, month, target):
    """ 
    Helper function returning the historical weather normal for a given month, target and city as a pandas dataframe.
    
    Args:
        x (pandas.Series): Row of a pandas dataframe, with a "city" column containing city names.
        city_normals (dict): Dictionary mapping all available cities to their respective historical temperature and precipitation values.
        month (int): Month for which to return the historical weather normals.
        target (str): Type of historical weather normal to be returned, e.g. tmin (minimum temperature), prcp (precipitation), ...
        
    Returns: 
        __ (pandas.DataFrame): Historical weather normal for a given month, target and city as a pandas dataframe.
        
    """
    return pd.DataFrame(city_normals[x.city]['Normals']).loc[month, target]


def plot_weather_on_route(city_normals, panam_cities, month, target):
    """
    Plots historical weather target for each city on geomap for a given month.
    
    Args:
        city_normals (dict): Dictionary mapping all available cities to their respective historical temperature and precipitation values.
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        month (int): Month for which to return the historical weather normals.
        target (str): Type of historical weather normal to be returned, e.g. tmin (minimum temperature), prcp (precipitation), ...
        
    Returns:
        selected_points (list[dict]): List of dictionaries containing user-selected point details (in case multiple overlapping points have
                                      been clicked, only first selected point will be taken into consideration). 
        city_map (dict): Mapping city's index to its full name.
        
    """
    temp_data = panam_cities.copy() 
    temp_data['target_per_month'] = temp_data.apply(lambda x: expand_dataframe(x, city_normals, month, target), axis = 1)
    temp_data = temp_data.sort_values(by='city')
    temp_data = temp_data.loc[~temp_data['target_per_month'].isna()]
    if target == 'prcp': 
        max_prcp = temp_data['target_per_month'].max() + 10 
        fig = go.Figure(data=go.Scattergeo(
            lat = temp_data.lat,
            lon = temp_data.lng,
            text = temp_data.city + ': ' + temp_data.target_per_month.astype(str) + ' mm',
            marker = dict(
                color = temp_data.target_per_month,
                colorscale = 'Blues',
                cmin = 0,
                cmax = max_prcp,
                reversescale = False,
                opacity = 1,
                size = 10,
                line=dict(width=1, color='DarkSlateGrey'),
                colorbar = dict(
                    titleside = "right",
                    outlinecolor = "rgba(68, 68, 68, 0)",
                    ticks = "outside",
                    showticksuffix = "last",
                    dtick = 50))))   
    else: 
        scl = [0,"rgb(0,0,255)"],[1/3,"rgb(255, 255, 255)"],[2/3, "rgb(255,255,0)"], [1,"rgb(255, 0, 0)"]
        fig = go.Figure(data=go.Scattergeo(
            lat = temp_data.lat,
            lon = temp_data.lng,
            text = temp_data.city + ': ' + temp_data.target_per_month.astype(str) + ' °C',
            marker = dict(
                color = temp_data.target_per_month,
                colorscale = scl,
                cmin = -20,
                cmax = 40,
                reversescale = False,
                opacity = 1,
                size = 10,
                line=dict(width=1, color='DarkSlateGrey'),
                colorbar = dict(
                    titleside = "right",
                    outlinecolor = "rgba(68, 68, 68, 0)",
                    ticks = "outside",
                    showticksuffix = "last",
                    dtick = 5))))
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        geo = dict(
            scope = 'world',
            showland = True,
            landcolor = "rgb(212, 212, 212)",
            subunitcolor = "rgb(255, 255, 255)",
            countrycolor = "rgb(255, 255, 255)",
            showlakes = True,
            lakecolor = "rgb(255, 255, 255)",
            showsubunits = True,
            showcountries = True,
            resolution = 50,
        ),
        title=f"Historical {target_dict[target]} in {month_dict[month]}",
    )
    fig.update_geos(fitbounds="locations", visible = False)
    city_map = temp_data.reset_index().city.to_dict()
    del temp_data
    selected_points = plotly_events(fig)
    return selected_points, city_map


def extract_middle_target(x, target):
    """ 
    Helper function extracting average temperature from a string of format "(min. temp.) avg. temp. (max. temp.)".
    
    Args:
        x (pandas.Series): Row of a pandas dataframe, containing average temperature as substring of target column value.
        target (str): Type of historical weather normal to be returned, e.g. tmin (minimum temperature), prcp (precipitation),...
        
    Returns: 
        __ (float): Average temperature extracted from input.
        
    """
    return float(x[target].split(') ')[-1].split(' (')[0])


def plot_final_route(panam_cities, route_df, target):
    """
    Plots historical weather target on estimated date of arrival for each city on geomap.
    
    Args:
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        route_df (pandas.DataFrame): Dataframe with one row per city, incl. respective estimated arrival date and estimated temperature in 
                                     columns.
        target (str): Type of historical weather normal to be returned, e.g. tmin (minimum temperature), prcp (precipitation), ... 
        
    Returns:
        selected_points (list[dict]): List of dictionaries containing user-selected point details (in case multiple overlapping points have
                                      been clicked, only first selected point will be taken into consideration). 
        city_map (dict): Mapping city's index to its full name.
        
    """
    temp_data = pd.merge(panam_cities, route_df, on = 'city', how = 'inner')
    temp_data['target_per_month'] = temp_data.apply(lambda x: extract_middle_target(x, target), axis = 1)
    temp_data = temp_data.sort_values(by='city')
    temp_data = temp_data.loc[~temp_data['target_per_month'].isna()]
    if target == 'prcp': 
        max_prcp = temp_data['target_per_month'].max() + 10
        fig = go.Figure(data=go.Scattergeo(
            lat = temp_data.lat,
            lon = temp_data.lng,
            text = temp_data.city + ': ' + temp_data.target_per_month.astype(str) + ' mm',
            marker = dict(
                color = temp_data.target_per_month,
                colorscale = 'Blues',
                cmin = 0,
                cmax = max_prcp,
                reversescale = False,
                opacity = 1,
                size = 10,
                line=dict(width=1, color='DarkSlateGrey'),
                colorbar = dict(
                    titleside = "right",
                    outlinecolor = "rgba(68, 68, 68, 0)",
                    ticks = "outside",
                    showticksuffix = "last",
                    dtick = 50))))
    else: 
        scl = [0,"rgb(0,0,255)"],[1/3,"rgb(255, 255, 255)"],[2/3, "rgb(255,255,0)"], [1,"rgb(255, 0, 0)"]
        fig = go.Figure(data=go.Scattergeo(
            lat = temp_data.lat,
            lon = temp_data.lng,
            text = temp_data.city + ': ' + temp_data.target_per_month.astype(str) + ' °C',
            marker = dict(
                color = temp_data.target_per_month,
                colorscale = scl,
                cmin = -20,
                cmax = 40,
                reversescale = False,
                opacity = 1,
                size = 10,
                line=dict(width=1, color='DarkSlateGrey'),
                colorbar = dict(
                    titleside = "right",
                    outlinecolor = "rgba(68, 68, 68, 0)",
                    ticks = "outside",
                    showticksuffix = "last",
                    dtick = 5))))
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        geo = dict(
            scope = 'world',
            showland = True,
            landcolor = "rgb(212, 212, 212)",
            subunitcolor = "rgb(255, 255, 255)",
            countrycolor = "rgb(255, 255, 255)",
            showlakes = True,
            lakecolor = "rgb(255, 255, 255)",
            showsubunits = True,
            showcountries = True,
            resolution = 50),
        title=f"Historical {target_dict[target]} along route")
    fig.update_geos(fitbounds="locations", visible = False)
    city_map = temp_data.reset_index().city.to_dict()
    del temp_data
    selected_points = plotly_events(fig)
    return selected_points, city_map


def display_route_map_and_table(city_normals, target_dict_UI, route_start_date, route_start_city, panam_cities):
    """
    Displays table containing one row per city, ordered along route, as well as estimated distance and travelling time to next stop, 
    estimated date of arrival and historical weather estimates for estimated date of arrival.
    
    Args:
        city_normals (dict): Dictionary containing the retrieved historical weather normals for each city. 
        target_dict_UI (dict): Mapping user-friendly labels for weather targets to their backend names, e.g. "Maximum temperature" to "tmax"
        route_start_date (date): Starting date of travel along route.
        route_start_city (str): Name of city to serve as route's starting point.
        panam_cities (pandas.DataFrame): Dataframe containing one row per city with respective geo-location provided in columns.
        
    Returns:
        route_df (pandas.DataFrame): Contains one row per city, ordered along route, as well as estimated distance and travelling time to
                                     next stop, estimated date of arrival and historical weather estimates for estimated date of arrival.
    
    """
    route_df = update_route_table(city_normals, route_start_date, route_start_city, panam_cities)
    st.write(route_df.rename(columns = {'city': 'City', 
                                      'est_dist': 'Est. distance\n(in km)', 
                                      'days_to_city': 'Est. time\n(in days)', 
                                      'arrival_date': 'Arrival date', 
                                      'tavg': 'Avg. Temperature\n(in °C)', 
                                      'tmin': 'Min. Temperature\n(in °C)', 
                                      'tmax': 'Max. Temperature\n(in °C)', 
                                      'prcp': 'Precipitation\n(in mm)', 
                                      'snow': 'Snowfall'}))
    show_route_plot = st.button('Show on map')
    route_target = target_dict_UI[st.selectbox('target', list(target_dict_UI.keys()), key = 'route_target', label_visibility = 'hidden')] 
    plot_final_route(panam_cities, route_df, route_target)
    return route_df
