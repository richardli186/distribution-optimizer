import math
import pandas as pd
import pulp as lp
import sys

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points on a sphere

    Inputs:
        - lat1: a real number representing the latitude coordinate in degrees of the first location
        - lon1: a real number representing the longitude coordinate in degrees of the first location
        - lat2: a real number representing the latitude coordinate in degrees of the second location
        - lon2: a real number representing the longitude coordinate in degrees of the second location

    Returns the distance in miles between the two points
    """
    r = 3959 #radius of Earth in miles

    #convert degrees to radians
    rad_lat1 = math.radians(lat1)
    rad_lon1 = math.radians(lon1)
    rad_lat2 = math.radians(lat2)
    rad_lon2 = math.radians(lon2)

    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1

    a = math.sin((dlat / 2) ** 2) + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin((dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    dist = r * c
    return dist

def cost_matrix(supply_nodes, demand_nodes):
    """
    If a cost csv isn't provided, builds a cost matrix based on the distance between two nodes

    Inputs:
        - supply_nodes: a pandas DataFrame representing the data from the supply nodes CSV
        - demand_nodes: a pandas DataFrame representing the data from the demand nodes CSV

    Returns a nested dictionary where each supply node corresponds to each demand node which 
    corresponds to the distance between the two 
    """
    suppliers = ['S_' + loc for loc in supply_nodes['name']]
    demanders = ['D_' + loc for loc in demand_nodes['name']]

    costs = []
    for s_row in supply_nodes.itertuples(index = False):
        sublist = []
        for d_row in demand_nodes.itertuples(index = False):
            dist = haversine(s_row.lat, s_row.lon, d_row.lat, d_row.lon)
            sublist.append(dist)
        costs.append(sublist)

    costs_dict = lp.makeDict([suppliers, demanders], costs, 0)
    return costs_dict

def load_cost_matrix(costs_df):
    """
    Converts a DataFrame into a nested dictionary

    Inputs:
        - costs_df: a DataFrame representing the costs of transportation from 
                each supply node to each demand node

    Returns a nested dictionary where each supply node corresponds to each demand node which 
    corresponds to the cost of transportation between the two 
    """
    costs_dict = {}
    for route in costs_df.itertuples(index = False):
        if 'S_' + route.supply not in costs_dict:
            costs_dict['S_' + route.supply] = {}
        costs_dict['S_' + route.supply]['D_' + route.demand] = route.cost
    return costs_dict

def validate_csv(df, required_columns, file_name):
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(
            f"{file_name} is missing required columns: "
            f"{', '.join(sorted(missing))}"
        )