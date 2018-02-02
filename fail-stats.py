#!/bin/env python3

from numpy import trapz
from utils import read_csv

def main(fails, obspop, minimal=False):
    # read input file
    obs_xs, obs_ys = read_csv(obspop)
    diskyears = trapz(obs_ys, x=obs_xs/24/365)
    with open(fails, 'rb') as f:
        f.seek(-20, 2)
        failcount = int(f.readlines()[-1].decode().split(',')[1])
    mean_afr = failcount/diskyears*100
    if minimal:
        print("{:.0f} {} {:.2f}%".format(diskyears, failcount, mean_afr))
    else:
        print("Total disk-years:", diskyears)
        print("Total failures:", failcount)
        print("Mean AFR: {}%".format(mean_afr))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute basic statistics from failure and observation data.')
    parser.add_argument('fails', help='cumulative failures (csv file)')
    parser.add_argument('obsct', help='observed population (csv file)')
    parser.add_argument('-m', '--minimal', dest='m', action='store_true',
                        help='Just output numbers')
    args = parser.parse_args()
    main(args.fails, args.obsct, minimal=args.m)
