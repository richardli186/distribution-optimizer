import pandas as pd
import pulp as lp

def apply_disruption(supply_dict, demand_dict, disruption_df):
    """
    Creates new supply and demand dictionaries incorporating the disruption scenario

    Inputs:
        - supply_dict: a dictionary representing the original supplier info, where each key
                       represents a location and each corresponding value represents its capacity
        - demand_dict: a dictionary representing the original demand info, where each key
                       represents a location and each corresponding value represents its demand
        - disruption_df: a DataFrame representing any supplier locations with capacity 
                         affected by the disruption
    """
    ds_supply_dict = supply_dict.copy()
    ds_demand_dict = demand_dict.copy()
    for ds in disruption_df.itertuples(index = False):
        if ds.type == 'supply':
            ds_supply_dict['S_' + ds.name] = ds.new_value
        if ds.type == 'demand':
            ds_demand_dict['D_' + ds.name] = ds.new_value
    return ds_supply_dict, ds_demand_dict