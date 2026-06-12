import pandas as pd
import argparse
import utils as ut
import pulp as lp
from disruption import apply_disruption

def solve_model(supply_dict, demand_dict, costs_dict, 
                output_file = 'outputs/results.csv', 
                lp_file = 'outputs/distribution_optimizer.lp'):
    """
    Creates the Lp problem, solves it, and prints the output

    Inputs:
        - supply_dict: a dictionary where each key represents the supply location 
                       and each corresponding value represents its capacity
        - demand_dict: a dictionary where each key represents the demand location 
                       and each corresponding value represents its demand
        - costs_dict: a nested dictionary where each key represents the supply location and
                      each corresponding value is a dictionary where each key represents the demand 
                      location and each value represents the cost of transportation between the two
    """
    #build Lp problem
    prob = lp.LpProblem('Distribution Optimizer', lp.LpMinimize)

    #lists of all supply nodes, demand nodes and possible routes
    supply_nodes = [s for s in supply_dict.keys()]
    demand_nodes = [d for d in demand_dict.keys()]
    routes = [(s, d) for s in supply_nodes for d in demand_nodes]

    #create Lp vars
    vars_dict = lp.LpVariable.dicts('Route', (supply_nodes, demand_nodes), 0, None, lp.LpInteger)

    #add objective function: lowest transport cost
    prob += lp.lpSum(costs_dict[s][d] * vars_dict[s][d] for s, d in routes), 'Lowest transportation cost'

    #add constraints
    for s in supply_nodes:
        prob += lp.lpSum(vars_dict[s][d] for d in demand_nodes) <= supply_dict[s], f'Supplied from {s}'

    for d in demand_nodes:
        prob += lp.lpSum(vars_dict[s][d] for s in supply_nodes) >= demand_dict[d], f'Received by {d}'

    #write and solve the problem
    prob.writeLP(lp_file)
    prob.solve(lp.PULP_CBC_CMD(msg=0))

    #print clean results to terminal and output
    print('Status = ', lp.LpStatus[prob.status])
    print(f"{'From':<20} {'To':<20} {'Units':>8}")
    print("-" * 50)
    for s in supply_nodes:
        for d in demand_nodes:
           val = lp.value(vars_dict[s][d])
           if val > 0:
               print(f"{s[2:]:<20} {d[2:]:<20} {val:>8.0f}")
    print('Total transportation cost = ', lp.value(prob.objective))

    rows = []
    for s in supply_nodes:
       for d in demand_nodes:
           val = lp.value(vars_dict[s][d])
           if val > 0:
               rows.append({'supply': s[2:], 'demand': d[2:], 'units': val})
    results_df = pd.DataFrame(rows)
    results_df.to_csv(output_file, index = False)

    return lp.value(prob.objective), results_df

def disruption_comparison(reg_results, ds_results, reg_cost, ds_cost):
    """
    Creates a text file showing the difference in units transported on each route

    Inputs:
        - reg_results: a DataFrame representing the units transported on each route in a regular scenario
        - ds_results: a DataFrame representing the units transported on each route in the disruption scenario
        - reg_cost: a real number representing the transportation cost in a regular scenario
        - ds_cost: a real number representing the transportation cost in the disruption scenario
    """
    df = reg_results.merge(ds_results, on = ['supply', 'demand'], how = 'outer')
    df = df.fillna(0)
    df['Route'] = df['supply'] + ' to ' + df['demand']
    df = df[df['units_x'] != df['units_y']]
    df.rename(columns = {'units_x': 'Regular Units', 'units_y': 'Disruption Units'}, inplace = True)
    df[['Route', 'Regular Units', 'Disruption Units']].to_csv('outputs/disruption_comparison.txt', index = False)

    with open('outputs/disruption_comparison.txt', 'a') as f:
        f.write(f'\nBaseline cost: {reg_cost:,.2f}\n')
        f.write(f'Disruption cost: {ds_cost:,.2f}\n')
        f.write(f'Change: {(ds_cost - reg_cost) / reg_cost:.1%}\n')

def main():
    parser = argparse.ArgumentParser(description = 'Supply chain distribution optimizer')
    
    parser.add_argument('--supply', required = True, help = 'Path to supply nodes CSV file')
    parser.add_argument('--demand', required = True, help = 'Path to demand nodes CSV file')
    parser.add_argument('--costs', required = False, help = 'Path to optional cost matrix CSV file')
    parser.add_argument('--disruption', required = False, help = 'Path to optional disruption scenario CSV file')
    
    args = parser.parse_args()
    
    s_df = pd.read_csv(args.supply)
    d_df = pd.read_csv(args.demand)

    #make sure csvs have necessary columns
    if args.costs:
        ut.validate_csv(s_df, ['name', 'supply'], 'Supply CSV')
        ut.validate_csv(d_df, ['name', 'demand'], 'Demand CSV')
    else:
        ut.validate_csv(s_df, ['name', 'lat', 'lon', 'supply'], 'Supply CSV')
        ut.validate_csv(d_df, ['name', 'lat', 'lon', 'demand'], 'Demand CSV')
    if args.costs: #if cost csv is provided
        costs_df = pd.read_csv(args.costs)
        ut.validate_csv(costs_df, ['supply', 'demand', 'cost'], 'Costs CSV')
        costs_dict = ut.load_cost_matrix(costs_df)
    else: #if cost csv is not provided
        costs_dict = ut.cost_matrix(s_df, d_df)
    
    supply_dict = {'S_' + name: cap for name, cap in zip(s_df['name'], s_df['supply'])}
    demand_dict = {'D_' + name: dem for name, dem in zip(d_df['name'], d_df['demand'])}
    reg_optimal_cost, reg_results = solve_model(supply_dict, demand_dict, costs_dict)

    if args.disruption: #if disruption scenario is provided
        disruption_df = pd.read_csv(args.disruption)
        ut.validate_csv(disruption_df, ['type', 'name', 'new_value'], 'Disruption CSV')
        ds_supply_dict, ds_demand_dict = apply_disruption(supply_dict, demand_dict, disruption_df)
        ds_optimal_cost, ds_results = solve_model(ds_supply_dict, ds_demand_dict, costs_dict, 
                                      output_file = 'outputs/disruption_results.csv',
                                      lp_file = 'outputs/disruption_optimizer.lp')
        
        percent_change = (ds_optimal_cost - reg_optimal_cost) / reg_optimal_cost
        print(f'The disruption increases the optimal total cost by {percent_change:.1%}, '
              f'from {reg_optimal_cost:,.2f} to {ds_optimal_cost:,.2f}')
        
        disruption_comparison(reg_results, ds_results, reg_optimal_cost, ds_optimal_cost)

if __name__ == '__main__':
    main()