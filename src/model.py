import pandas as pd
import argparse
import utils as ut
import pulp as lp

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
    ut.validate_csv(s_df, ['name', 'city', 'state', 'lat', 'lon', 'supply'], "Supply CSV")
    ut.validate_csv(d_df, ['name', 'city', 'state', 'lat', 'lon', 'demand'], "Demand CSV")
    if args.costs: #if cost csv is provided
        costs_raw = pd.read_csv(args.costs)
        ut.validate_csv(costs_raw, ['supply', 'demand', 'cost'], 'Costs CSV')
        costs_dict = ut.load_cost_matrix(costs_raw)
    else: #if cost csv is not provided
        costs_dict = ut.cost_matrix(s_df, d_df)
    
    disruption_df = pd.read_csv(args.disruption) if args.disruption else None #if disruption file is/isn't provided

    #build Lp problem
    prob = lp.LpProblem('Distribution Optimizer', lp.LpMinimize)

    supply_dict = {'S_' + name: cap for name, cap in zip(s_df['name'], s_df['supply'])}
    demand_dict = {'D_' + name: dem for name, dem in zip(d_df['name'], d_df['demand'])}

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
    prob.writeLP('outputs/distribution_optimizer.lp')
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
    results_df.to_csv('outputs/results.csv', index=False)

if __name__ == '__main__':
    main()