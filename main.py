"""
Main file containing the Streamlit application.
"""

import streamlit as st
import pandas as pd
import numpy as np
from data_utils import * 
from weather_utils import *
from plotting_utils import * 
import os
from datetime import datetime, date, timedelta
from fpdf import FPDF
import base64

# Dictionaries mapping user-friendly labels for input components to their backend names            
target_dict_UI = {'Average Temperature': 'tavg', 'Maximum Temperature': 'tmax', 'Minimum Temperature': 'tmin', 'Precipitation': 'prcp'}
month_dict_UI = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6,
                 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}

st.set_page_config(layout="wide")

st.title('Roadtrip Weather Planning Tool')

# Data Loading
data_load_state = st.text('Loading data...')
available_cities, panam_cities, city_normals, st_warnings = load_data()
data_load_state.text("Data loaded.")
col0, _ = st.columns([2, 1]) 
with col0:
    with st.expander('Data Availability'):
        for i in range(len(st_warnings)):
            st.write(st_warnings[i])

# Define components for adding and removing cities from route
col1a, col2a, _ = st.columns([1, 1, 1]) 
with col1a:
    with st.form(key='add_city'):
        st.write("Add a city")
        new_country = st.selectbox('Select country', sorted(list(cities.keys())))
        new_change = st.form_submit_button("Select")
        if new_change:
            new_city = st.selectbox('Select city', available_cities[new_country])        
            submitted_new_city = st.form_submit_button(label='Add city')#, on_click=add_city(new_city))
            if submitted_new_city:
                load_data.clear()
                cities, panam_cities, city_normals = add_city(cities, panam_cities, city_normals, new_country, new_city)
                st.write(new_city+' in '+new_country+' has been added.')
with col2a:
    with st.form(key='remove_city'):
        st.write("Remove a city")
        old_country = st.selectbox('Select country', sorted(list(cities.keys())))
        old_change = st.form_submit_button("Select")
        if old_change:
            old_city = st.selectbox('Select city', sorted(list(cities[old_country])))        
            removed_old_city = st.form_submit_button(label='Remove city')#, on_click=remove_city(old_city))
            if removed_old_city:
                load_data.clear()
                cities, panam_cities, city_normals = remove_city(cities, panam_cities, city_normals, old_country, old_city)
                #load_data.clear()
                st.write(old_city+' in '+old_country+' has been removed.')
            
# User input components allowing selection of month and target (e.g. max. temperature, precipitation, ...) to be displayed on a map
col1b, _ = st.columns([2, 1]) 
with col1b:
    target = target_dict_UI[st.selectbox('Target', list(target_dict_UI.keys()))] #'tavg' #
    month = month_dict_UI[st.select_slider('Month', options = list(month_dict_UI.keys()))] 
city = ''

# Visualization of historical weather per month on a geo map (left) and individual yearly weather per selected city (right)
col1, col2 = st.columns([2, 1]) 
with col1:
    selected_points, city_map = plot_weather_on_route(city_normals, panam_cities, month, target)
    if len(selected_points)>0:
        city = city_map[selected_points[0]['pointNumber']]
    else:
        pass
with col2:
    if city != '':
        plot_temp_per_city(city_normals, city)
        plot_rain_per_city(city_normals, city) 
    else:
        pass
    
# Route planning component picking direct route between cities and showing historical weather based on driving time estimations by user
st.subheader('Route Planning')

# User input components for estimated start date and preferred starting point
panam_start = st.date_input("Start date of Panamericana", datetime(2023, 1, 1))
route_start = st.selectbox('Select starting point of Panamericana', list(panam_cities.city.sort_values().values))

# Table displaying stops along the route as rows with aerial distance and estimated travelling time (provided by user) in columns 
display_route = st.button('Get route')
st.write('Please enter estimated number of days between stops.')
route_df = get_route(panam_start, route_start, panam_cities)
route_table = st.experimental_data_editor(route_df[['city','est_dist', 'days_to_city']]\
                                          .rename(columns = {'city': 'City',
                                                             'est_dist': 'Estimated distance (in km)', 
                                                             'days_to_city': 'Estimated travelling time (in days)'}), 
                                          num_rows='dynamic', 
                                          key = 'route_table_edits')
update_dates = st.button('Update table', key="update_dates")

# Final route table displaying stops as rows and additional information such as estimated date of arrival and historical weather in columns
if st.session_state.get("update_dates"):
    final_route_df = display_route_map_and_table(city_normals, target_dict_UI, panam_start, route_start, panam_cities)
    
# Include sources for external data
st.text('GPS database provided by SimpleMaps: \n - USA: https://simplemaps.com/data/us-cities. \n - Canada: https://simplemaps.com/data/canada-cities. \n - Mexico, Guatemala, El Salvador, Nicaragua, Costa Rica, Panama, Colombia, Ecuador, Peru, Chile, Argentina, Uruguay: Covered under MIT license')
st.text('Weather data provided by Meteostat: https://meteostat.net')
