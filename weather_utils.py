"""
Backend functions retrieving historical weather data online and adding relevant weather normals per city.
"""

import pandas as pd
from meteostat import Stations, Daily, Normals
from tqdm.auto import tqdm
import calendar
from datetime import datetime

# Specify timeframe for which to retrieve/substitute the historical weather normals
START_YEAR = 1991
END_YEAR = 2020


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
    

def get_normals_per_city(x):
    """
    Retrieves historical weather normals from Meteostat API for a single city.
    
    Args:
        x (pandas.Series): Row of pandas dataframe containing the geo coordinates for a given city.
        
    Returns:
        city_normals (dict): Dictionary containing the retrieved historical weather normals for the given city. In case no weather normals 
                             are available, the ID of the closest weather station will still be returned and the field "Missing" will be 
                             set to True.
        
    """
    stations = Stations()
    # Get closest weather station to geo coordinates associated with input city
    station = stations.nearby(lat = x['lat'], lon = x['lng']).fetch(1)
    station_id = station.index[0]
    # Retrieve normals for closest weather station
    data = Normals(station_id, START_YEAR, END_YEAR)
    data = data.fetch()
    if len(data) == 0:
        print(f'No normals available for {x.city}.')
        missing = True
    else:
        missing = False
    city_normals = {'Station ID': station_id, 'Normals': data.to_dict(), 'Timespan': f'{START_YEAR}-{END_YEAR}', 'Missing': missing}
    return city_normals


#def add_normals(df):
#    """ Legacy function. """
#    tqdm.pandas(position=0, leave=True)
#    df[['Station Id', 'Normals', 'Timespan', 'Missing']] = pd.DataFrame(df.progress_apply(lambda x: get_normals_per_city(x), 
#                                                                                          axis = 1).tolist())
#    return df


def get_historical_dailies(station_id, day, month):
    """
    Retrieves historical weather for a specific day and specific weather station from Meteostat API. The weather data will be collected 
    for all years between global variables START_YEAR and END_YEAR.
    
    Args:
        station_id (str): ID of Meteostat weather station.
        day (int): Day for which to retrieve the historical weather information, e.g. 20 for April 20th.
        month (int): Month for which to retrieve the historical weather information, e.g. 4 for April 20th.
        
    Returns:
        daily_avgs (pandas.Series): Series containing the historical average weather data for the day specified, as well as information on 
                                    potentially missing years in the data.
        
    """    
    last_available_dailies = pd.concat([Daily(station_id, datetime(year, month, day), datetime(year, month, day)).fetch() 
                                        for year in range(START_YEAR, END_YEAR)])

    available_years = len(last_available_dailies)
    daily_avgs = last_available_dailies[['tavg', 'tmin', 'tmax', 'prcp', 'snow']].mean()
    daily_avgs['available_years'] = available_years
    daily_avgs['min_year_available'] = last_available_dailies.index.min().year
    daily_avgs['max_year_available'] = last_available_dailies.index.max().year
    if available_years < 10:
        print(f'{bcolors.FAIL}WARNING: Less than 10 years of weather data available for station ID {station_id}.{bcolors.ENDC}')
    return daily_avgs


def get_monthly_normal_substitutes(station_id, month):
    """
    Substitutes monthly weather data for cities with missing Meteostat normals by retrieving and averaging historical daily weather data.
    
    Args:
        station_id (str): ID of Meteostat weather station.
        month (int): Month for which to retrieve the historical weather information, e.g. 4 for April.
        
    Returns:
        monthly_avgs (pandas.Series): Series containing the historical average weather data for the month specified, as well as information
                                      on potentially missing years in the data.
                                      
    """
    last_available_dailies = pd.concat([Daily(station_id, 
                                              datetime(year, month, 1), 
                                              datetime(year, month, calendar.monthrange(year, month)[-1])).fetch() 
                                        for year in range(START_YEAR, END_YEAR)])
    if len(last_available_dailies) == 0:
        monthly_avgs = {'available_years': 0}
        return monthly_avgs
    else:
        available_years = len(last_available_dailies.index.year.drop_duplicates())
        monthly_avgs = last_available_dailies[['tavg', 'tmin', 'tmax', 'prcp']].mean().round(1)
        monthly_avgs['available_years'] = available_years
        monthly_avgs['min_year_available'] = last_available_dailies.index.min().year
        monthly_avgs['max_year_available'] = last_available_dailies.index.max().year
        return monthly_avgs


def get_normal_substitutes(city, station_id):
    """
    Substitutes weather data for cities with missing Meteostat normals by retrieving and averaging historical daily weather data.
    
    Args:
        city (str): Name of city for which to retrieve weather data.
        station_id (str): ID of closest Meteostat weather station.
        
    Returns:
        months_dict (dict): Dictionary mapping each month to its respective historical average weather data.
        st_warning (str): Warning message in case only few years were available to calculate the historical weather averages.
                                      
    """
    month_dicts = {}
    for month in range(1,13):
        month_dicts[month] = get_monthly_normal_substitutes(station_id, month)
    months_dict = pd.DataFrame(month_dicts).T.to_dict()
    st_warning = ''
    if min(months_dict['available_years'].values()) == 0:
        print(f'{bcolors.FAIL}WARNING: No weather data available for {city}.{bcolors.ENDC}')
    elif min(months_dict['available_years'].values()) < 10:
        st_warning = f'Only {int(min(months_dict["available_years"].values()))} years of weather data available for {city}.'
    return months_dict, st_warning
