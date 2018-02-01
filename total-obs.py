#!/bin/env python3

from numpy import trapz
from utils import read_csv

def main(obspop_file):
    # read input file
    obs_xs, obs_ys = read_csv(obspop_file)
    print("{:.0f}".format(trapz(obs_ys, x=obs_xs/24/365)))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compute total disk-years observed, given the observed population over age.')
    parser.add_argument('obspop', metavar='OBSPOP', help='observed population (csv file)')
    args = parser.parse_args()
    main(args.obspop)
