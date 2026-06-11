import pandas as pd
import argparse
import utils as ut

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

    costs_df = pd.read_csv(args.costs) if args.costs else ut.cost_matrix(s_df, d_df) #if cost file is/isn't provided
    disruption_df = pd.read_csv(args.disruption) if args.disruption else None #if disruption file is/isn't provided

if __name__ == '__main__':
    main()